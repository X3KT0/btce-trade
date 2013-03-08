import httplib
import urllib
import urllib2
import json
import hashlib
import hmac
import time
import copy
import string
import Queue
import threading


#'BTC-E Informer. v.1.0 beta'
#'(C) Jan-2013 ob1kenobi (skype aldis.rigerts)'
#'Donate BTC: 16mSMKbNNpEJc1GasDb1JN5FzNnNYCgpdy'
#'Donate LTC: LbNS12qcjGr8LjS23TvnpbGu3FPFJpFZPj'


prs=['btc_usd', 'btc_rur', 'btc_eur', 'ltc_btc', 'ltc_usd', 'ltc_rur', 'nmc_btc', 'usd_rur', 'eur_usd', 'nvc_btc']
prs_txt=['btc_usd', 'btc_rur', 'btc_eur', 'ltc_btc', 'ltc_usd', 'ltc_rur', 'nmc_btc', 'usd_rur', 'eur_usd', 'nvc_btc']
ro={'btc_usd':3, 'btc_rur':4, 'btc_eur':8, 'ltc_btc':5, 'ltc_usd':6, 'ltc_rur':5, 'nmc_btc':5, 'usd_rur':5, 'eur_usd':5, 'nvc_btc':5}

pair_sel=1

frm_rate={'btc_usd':'{0:10.3f}', 'btc_rur':'{0:10.4f}', 'btc_eur':'{0:10.5f}',
          'ltc_btc':'{0:10.5f}', 'ltc_usd':'{0:10.6f}', 'ltc_rur':'{0:10.5f}',
          'nmc_btc':'{0:10.5f}', 'usd_rur':'{0:10.5f}', 'eur_usd':'{0:10.5f}',
          'nvc_btc':'{0:10.5f}'}

tick_now={}
tick_old={}
for pair in prs:
    tick_now[pair]={}
    tick_old[pair]={}

lbls=[[0 for x in xrange(5)] for x in xrange(15)]

f1=('Bookman Old Style', 11)
f2=('Calibri', 10)
f3=('Courier New', 11)

queue_inp=Queue.Queue(20)
queue_out=Queue.Queue(20)
queue_tmp=Queue.Queue(20)

queue_ord_i=Queue.Queue(20)
queue_ord_o=Queue.Queue(20)


my_frm={}
my_cmd={}
my_orders={}

zzz=0

BTC_key=''
BTC_secret=''

first_run=1


lbl_sell_ord=[0 for x in xrange(20)]

#lbls2={'se':[0 for x in xrange(20)]}
lbls2={'so_sum':{}, 'so_siz':{}, 'so_bid':{},
       'bo_sum':{}, 'bo_siz':{}, 'bo_ask':{}}


from Tkinter import *
#from Tkinter import ttk
#from ttk import *
#import ttk
import tkMessageBox

#from PIL import Image, ImageTk


class MyWin:

    visible=1
    row=0

    def __init__(self, parent, i, cmd_txt='Test'):

        self.row=i*2
        
        #make button
        self.cmd=Button(parent, text=cmd_txt, command=self.ch_size)
        self.cmd.grid(row=self.row+1, column=0, sticky=E+W)
        
        #make frame
        self.frm=Frame(parent, width=384, height=0, borderwidth=0, relief=GROOVE)
        self.frm.grid_propagate(0)
        self.frm.grid(row=self.row+2)
        self.frm.grid_forget()

        self.visible=0

    def ch_size(self):
        
        if self.visible==1:
            self.frm.grid_forget()
            self.visible=0
        else:
            self.frm.grid(row=self.row+2)
            self.visible=1



class CancelOrder:

    order_no=0

    def __init__(self, parent, n, cmd_txt='Cancel'):

        self.order_no=n
       
        #make button
        self.cmd=Button(parent, text=cmd_txt, command=self.stop_it)

    def stop_it(self):
        print 'Order no =', self.order_no
        try:
            cancel_order(self.order_no)
        except:
            print 'Cancel failed!'
        

    
class App:

    def __init__(self, master):
        global im_logo, image, lbls, prs, my_cmd, my_frm, pair_sel

        self.master=master
        self.cur_prs=-2

        self.frame_pairs = Frame(master, width=800, height=34, borderwidth=3, relief=GROOVE)
        self.frame_pairs.grid_propagate(0)
        self.frame_pairs.grid(row=0, column=0, columnspan=2, padx=3, pady=3)

        self.pair_sel=IntVar(master=master)
        self.pair_sel.set(0)
        for i in range(0, len(prs)):
            pair=prs[i]
            txt=string.upper(pair[0:3])+'/'+string.upper(pair[4:7])
            r=Radiobutton(self.frame_pairs, text=txt, variable=self.pair_sel, value=i,
                          indicatoron=0, font=f2, command=self.change_pair)
            #if i==self.pair_sel:
            #    r.select()
            r.grid(row=0, column=i, padx=5)
        


        self.frame_chart = Frame(master, width=800, height=260-100, borderwidth=3, relief=GROOVE)
        self.frame_chart.grid_propagate(0)
        self.frame_chart.grid(row=1, column=0, columnspan=2, padx=3, pady=3)

        self.frame_1 = Frame(master, width=400-3, height=380+4+6+100, borderwidth=3, relief=GROOVE)
        self.frame_1.grid_propagate(0)
        self.frame_1.grid(row=2, column=0, padx=3, pady=3)

        self.frame_2 = Frame(master, width=400-3, height=380+4+6+100, borderwidth=3, relief=GROOVE)
        self.frame_2.grid_propagate(0)
        self.frame_2.grid(row=2, column=1, padx=3, pady=3)

        self.frame_top = Frame(master, width=400-10, height=690+6, borderwidth=3, relief=GROOVE)
        self.frame_top.grid_propagate(0)
        self.frame_top.grid(row=0, column=2, sticky=E+W, rowspan=3, padx=3, pady=3)

        self.frame_1_x = Frame(self.frame_1, width=400-3-6, height=0, borderwidth=0, relief=GROOVE)
        self.frame_1_x.grid_propagate(0)
        self.frame_1_x.grid(row=0, column=0)

        self.frame_2_x = Frame(self.frame_2, width=400-3-6, height=0, borderwidth=0, relief=GROOVE)
        self.frame_2_x.grid_propagate(0)
        self.frame_2_x.grid(row=0, column=0)

        self.frame_top_x = Frame(self.frame_top, width=384, height=0, borderwidth=0, relief=GROOVE)
        self.frame_top_x.grid_propagate(0)
        self.frame_top_x.grid(row=0, column=0)

        #self.frame = Frame(master, width=400, height=550)
        #self.frame.grid(row=1)
        
        #image = Image.open("btce_logo.png")
        #im_logo = ImageTk.PhotoImage(image)

        #lbl1=Label(self.frame, image=im_logo).grid(row=0, columnspan=2)

        #self.cmd1=Button(self.frame_top, text='Change size', command=self.ch_size)
        #self.cmd1.grid(row=0, column=0)

        my_frm[0]=MyWin(parent=self.frame_top, i=0, cmd_txt='Rates')
        my_frm[1]=MyWin(parent=self.frame_top, i=1, cmd_txt='Settings')

        my_frm[2]=MyWin(parent=self.frame_1, i=0, cmd_txt='Buy')
        my_frm[3]=MyWin(parent=self.frame_1, i=1, cmd_txt='My sell orders')
        my_frm[4]=MyWin(parent=self.frame_1, i=2, cmd_txt='Sell Orders')

        my_frm[5]=MyWin(parent=self.frame_2, i=0, cmd_txt='Sell')
        my_frm[6]=MyWin(parent=self.frame_2, i=1, cmd_txt='My buy orders')
        my_frm[7]=MyWin(parent=self.frame_2, i=2, cmd_txt='Buy Orders')

        self.init_settings(parent=my_frm[1].frm)
        self.fill_sell_orders(parent=my_frm[4].frm, parent2=my_frm[7].frm)

        self.init_buy_sell(parent=my_frm[2].frm, parent2=my_frm[5].frm)


        #self.in_frame(parent=self.frame_top, cmd='init', i=0)
        #self.in_frame(parent=self.frame_top, cmd='init', i=1)

##        self.tree=ttk.Treeview(my_frm[1].frm)
##        self.tree['columns']=('Pair', 'sell', 'avg', 'buy', 'spread')
##        self.tree.column('#0',width=1, stretch=False)
##        self.tree.column('Pair',width=60, anchor='center')
##        self.tree.heading('Pair',text='Pair')
##        self.tree.column('sell',width=60, anchor='center')
##        self.tree.column('avg',width=60, anchor='center')
##        self.tree.column('buy',width=60, anchor='center')
##        self.tree.column('spread',width=60, anchor='center')
##        self.tree.grid(row=0, column=0)
##        self.tree.insert(parent='', index='end', iid='top1', values=('value1'))
##        self.tree.insert(parent='', index='end', values=('value2'))
##        self.tree.insert(parent='', index='end', values=('value3'))

        #self.frame
        label1=Label(my_frm[0].frm, text="Pair:")
        label1.grid(row=2, column=0)
        label1.config(font=f2, fg='darkgrey')
        Label(my_frm[0].frm, text=" sell", font=f2, fg='darkgrey').grid(row=2, column=1)
        Label(my_frm[0].frm, text=" avg", font=f2, fg='darkgrey').grid(row=2, column=2)
        Label(my_frm[0].frm, text=" buy", font=f2, fg='darkgrey').grid(row=2, column=3)
        Label(my_frm[0].frm, text=" spread", font=f2, fg='darkgrey').grid(row=2, column=4)
        Label(my_frm[0].frm, text="          ", font=f2, fg='darkgrey').grid(row=2, column=5)

        for pair in prs:
            k=prs.index(pair)
            for c in range(5):
                lbls[k][c]=Label(my_frm[0].frm, text=' ', font=f1, fg='black')
                lbls[k][c].grid(row=k+3, column=c)


        self.master.after(1000, self.do_iter)
        self.master.after(2000, self.put_next_task)

    def change_pair(self):
        self.update_sell_orders()
        self.print_orders(parent=my_frm[3].frm, parent2=my_frm[6].frm)


    def print_orders(self, parent, parent2):


        g=parent.grid_slaves()
        for slave in g:
            slave.grid_forget()
            slave.destroy()

        g=parent2.grid_slaves()
        for slave in g:
            slave.grid_forget()
            slave.destroy()

        p=self.pair_sel.get()
        pair=prs[p]

        try:
            x=my_orders['return']
        except:
            return


        Label(parent, text=" Command ", font=f2, fg='darkgrey').grid(row=0, column=0)
        Label(parent, text=" Size ", font=f2, fg='darkgrey').grid(row=0, column=1)
        Label(parent, text=" Bid ", font=f2, fg='darkgrey').grid(row=0, column=2)

        i=0
            
        for o in x:
            if x[o][u'pair'] != pair:
                continue
            if x[o][u'type'] != 'sell':
                continue
            
            #print o, x[o]
            #oo=int(o)
            i=i+1
            txt2='{0:15.8f}'.format(x[o][u'amount'])
            txt3=frm_rate[pair].format(x[o]['rate'])
            
            y=CancelOrder(parent=parent, n=o)
            y.cmd.grid(row=i, column=0)
            Label(parent, text=txt2, font=f3, fg='black').grid(row=i, column=1)
            Label(parent, text=txt3, font=f3, fg='black').grid(row=i, column=2)

        Label(parent2, text=" Ask ", font=f2, fg='darkgrey').grid(row=0, column=0)
        Label(parent2, text=" Size ", font=f2, fg='darkgrey').grid(row=0, column=1)
        Label(parent2, text=" Command ", font=f2, fg='darkgrey').grid(row=0, column=2)

        i=0
        for o in x:
            if x[o][u'pair'] != pair:
                continue
            if x[o][u'type'] != 'buy':
                continue
            
            #print o, x[o]
            i=i+1
            txt2='{0:15.8f}'.format(x[o][u'amount'])
            txt3=frm_rate[pair].format(x[o]['rate'])

            y=CancelOrder(parent=parent2, n=o)
            y.cmd.grid(row=i, column=2)
            Label(parent2, text=txt2, font=f3, fg='black').grid(row=i, column=1)
            Label(parent2, text=txt3, font=f3, fg='black').grid(row=i, column=0)

        
    def init_settings(self, parent):

        self.api_key=StringVar()
        self.api_secret=StringVar()

        
        Label(parent, text="API key:", font=f2, fg='darkgrey').grid(row=0, column=0, sticky=W)
        e1=Entry(parent, font=f2, width=50, textvariable=self.api_key)
        e1.grid(row=1, column=0, sticky=W)
        
        Label(parent, text="API secret:", font=f2, fg='darkgrey').grid(row=2, column=0, sticky=W)
        e2=Entry(parent, font=f2, width=50, textvariable=self.api_secret)
        e2.grid(row=3, column=0, sticky=W)

        Label(parent, text=" ").grid(row=4, column=0)
        Button(parent, text=' Use these API settings! ', command=self.chg_api).grid(row=5, column=0)

    def chg_api(self):
        global BTC_key, BTC_secret
        BTC_key = self.api_key.get()
        BTC_secret = self.api_secret.get()
        #print x,y

        if BTC_key=='' or BTC_secret=='':
            tkMessageBox.showinfo("Error!", "No Key or Secret")
            return
        
        my_frm[2].ch_size()
        my_frm[5].ch_size()


    def init_buy_sell(self, parent, parent2):
        self.buy_am=StringVar()
        self.buy_pr=StringVar()

        Label(parent, text=" Amount ", font=f2, fg='darkgrey').grid(row=0, column=0, sticky=W)
        e1=Entry(parent, font=f3, width=20, textvariable=self.buy_am)
        e1.grid(row=1, column=0, sticky=W)
        
        Label(parent, text=" Price ", font=f2, fg='darkgrey').grid(row=2, column=0, sticky=W)
        e1=Entry(parent, font=f3, width=20, textvariable=self.buy_pr)
        e1.grid(row=3, column=0, sticky=W)

        Label(parent, text="   ", font=f2, fg='darkgrey').grid(row=8, column=0, sticky=W)
        Button(parent, text=' Buy! ', command=self.buy_now).grid(row=9, column=0)
        Label(parent, text="   ", font=f2, fg='darkgrey').grid(row=10, column=0, sticky=W)


        self.sell_am=StringVar()
        self.sell_pr=StringVar()

        Label(parent2, text=" Amount ", font=f2, fg='darkgrey').grid(row=0, column=0, sticky=W)
        e1=Entry(parent2, font=f3, width=20, textvariable=self.sell_am)
        e1.grid(row=1, column=0, sticky=W)
        
        Label(parent2, text=" Price ", font=f2, fg='darkgrey').grid(row=2, column=0, sticky=W)
        e1=Entry(parent2, font=f3, width=20, textvariable=self.sell_pr)
        e1.grid(row=3, column=0, sticky=W)

        Label(parent2, text="   ", font=f2, fg='darkgrey').grid(row=8, column=0, sticky=W)
        Button(parent2, text=' Sell! ', command=self.sell_now).grid(row=9, column=0)
        Label(parent2, text="   ", font=f2, fg='darkgrey').grid(row=10, column=0, sticky=W)



    def buy_now(self):
        am_txt=self.buy_am.get()
        pr_txt=self.buy_pr.get()
        try:
            am=float(am_txt)
            pr=float(pr_txt)
        except:
            tkMessageBox.showinfo("Error!", "Not a number in amount or price.")
            return
        
        p=self.pair_sel.get()
        pair=prs[p]

        print am, pr, pair, round(pr, ro[pair]), round(am,8)

        try:
            z=trade('buy', round(pr, ro[pair]), round(am,8), pair)
            if z['success']!=1:
                raise
        except:
            tkMessageBox.showinfo("Error!", "Order did not accepted, try once more.")
            return
        
        self.buy_am.set('')
        self.buy_pr.set('')




    def sell_now(self):
        am_txt=self.sell_am.get()
        pr_txt=self.sell_pr.get()
        try:
            am=float(am_txt)
            pr=float(pr_txt)
        except:
            tkMessageBox.showinfo("Error!", "Not a number in amount or price.")
            return
        
        p=self.pair_sel.get()
        pair=prs[p]

        print am, pr, pair, round(pr, ro[pair]), round(am,8)

        try:
            z=trade('sell', round(pr, ro[pair]), round(am,8), pair)
            if z['success']!=1:
                raise
        except:
            tkMessageBox.showinfo("Error!", "Order did not accepted, try once more.")
            return
        
        self.sell_am.set('')
        self.sell_pr.set('')

        
       

    def fill_sell_orders(self, parent, parent2):
        global lbls2


        Label(parent, text=" Sum ", font=f2, fg='darkgrey').grid(row=0, column=0)
        Label(parent, text=" Size ", font=f2, fg='darkgrey').grid(row=0, column=1)
        Label(parent, text=" Bid ", font=f2, fg='darkgrey').grid(row=0, column=2)
        for i in range(0,19):
            lbls2['so_sum'][i]=Label(parent, text=' ', font=f3, fg='darkgrey')
            lbls2['so_sum'][i].grid(row=i+1, column=0)
            
            lbls2['so_siz'][i]=Label(parent, text=' ', font=f3, fg='black')
            lbls2['so_siz'][i].grid(row=i+1, column=1)
            
            lbls2['so_bid'][i]=Label(parent, text=' ', font=f3, fg='black')
            lbls2['so_bid'][i].grid(row=i+1, column=2)

        Label(parent2, text=" Ask ", font=f2, fg='darkgrey').grid(row=0, column=0)
        Label(parent2, text=" Size", font=f2, fg='darkgrey').grid(row=0, column=1)
        Label(parent2, text=" Sum ", font=f2, fg='darkgrey').grid(row=0, column=2)
        for i in range(0,19):
            lbls2['bo_ask'][i]=Label(parent2, text=' ', font=f3, fg='black')
            lbls2['bo_ask'][i].grid(row=i+1, column=0)
            
            lbls2['bo_siz'][i]=Label(parent2, text=' ', font=f3, fg='black')
            lbls2['bo_siz'][i].grid(row=i+1, column=1)
            
            lbls2['bo_sum'][i]=Label(parent2, text=' ', font=f3, fg='darkgrey')
            lbls2['bo_sum'][i].grid(row=i+1, column=2)

            

    def update_sell_orders(self):
        global lbls2

        p=self.pair_sel.get()
        pair=prs[p]
        s=0
        for i in range(0,19):
            try:
                txt1=frm_rate[pair].format(tick_now[pair]['asks'][i][0])
                txt2='{0:15.8f}'.format(tick_now[pair]['asks'][i][1])
                s=s+tick_now[pair]['asks'][i][1]
                txt3='{0:15.8f}'.format(s)
            except:
                txt1=' '
                txt2=' '
                txt3=' '

            lbls2['so_bid'][i].config(text=txt1)
            lbls2['so_siz'][i].config(text=txt2)
            lbls2['so_sum'][i].config(text=txt3)

        s=0
        for i in range(0,19):
            try:
                txt1=frm_rate[pair].format(tick_now[pair]['bids'][i][0])
                txt2='{0:15.8f}'.format(tick_now[pair]['bids'][i][1])
                s=s+tick_now[pair]['bids'][i][1]
                txt3='{0:15.8f}'.format(s)
            except:
                txt1=' '
                txt2=' '
                txt3=' '
                
            lbls2['bo_ask'][i].config(text=txt1)
            lbls2['bo_siz'][i].config(text=txt2)
            lbls2['bo_sum'][i].config(text=txt3)



    def do_iter(self):
        global lbls, prs, my_cmd, my_frm, lbl_sell_ord

            

        if queue_out.empty():
            self.master.after(200, self.do_iter)
            return
            
        r=queue_out.get()
        pair=r['pair']
        if r['done']:
            tick_old[pair]=copy.deepcopy(tick_now[pair])
            tick_now[pair]=r
            if tick_old[pair]=={}:
                tick_old[pair]=copy.deepcopy(tick_now[pair])

            k=prs.index(pair)
            txt=string.upper(pair[0:3])+'/'+string.upper(pair[4:7])
            lbls[k][0].config(text=txt)
            
            txt=frm_rate[pair].format(tick_now[pair]['buy'])
            lbls[k][1].config(text=txt, font=f2, fg=get_fg(pair,'buy'))
                              
            txt=frm_rate[pair].format(tick_now[pair]['my_avg'])
            lbls[k][2].config(text=txt, font=f1, fg=get_fg(pair,'my_avg'))
                              
            txt=frm_rate[pair].format(tick_now[pair]['sell'])
            lbls[k][3].config(text=txt, font=f2, fg=get_fg(pair,'sell'))
            
            txt='{0:8.2f}%'.format(tick_now[pair]['spread'])
            lbls[k][4].config(text=txt, font=f2, fg=get_fg(pair,'spread'))

        p=self.pair_sel.get()
        if pair==prs[p]:
            self.update_sell_orders()
            
        queue_tmp.put(pair)
        self.master.after(200, self.do_iter)
           

            
    def put_next_task(self):
        global my_orders, first_run

        if first_run==1:
            first_run=0
            my_frm[0].ch_size()
            my_frm[1].ch_size()
            #my_frm[2].ch_size()
            my_frm[3].ch_size()
            my_frm[4].ch_size()
            #my_frm[5].ch_size()
            my_frm[6].ch_size()
            my_frm[7].ch_size()

        
        
        if not queue_ord_o.empty():
            r=queue_ord_o.get()
            #print r['done']
            if r['done']:
                my_orders=copy.deepcopy(r)
                #print my_orders['return']
                self.print_orders(parent=my_frm[3].frm, parent2=my_frm[6].frm)
                
            queue_ord_i.put('go')

        if not queue_tmp.empty():
            p=queue_tmp.get()
            queue_inp.put(p)
            
        self.master.after(1*1000, self.put_next_task)
        






class ThreadTick(threading.Thread):
    def __init__(self, queue_inp, queue_out):
        threading.Thread.__init__(self)
        self.queue_inp=queue_inp
        self.queue_out=queue_out

    def run(self):
        z={}
        while True:
            pair=self.queue_inp.get()
            url='https://btc-e.com/api/2/'+pair+'/depth'
            try:
                req = urllib2.Request(url)
                opener = urllib2.build_opener()
                f = opener.open(req)
                x=f.read()
                y=json.loads(x)
                z=copy.deepcopy(y)
                z['buy']=z['asks'][0][0]
                z['sell']=z['bids'][0][0]

                
                z['my_avg']=(z['sell']+z['buy'])/2.0
                z['spread']=((1.0*z['buy'])/z['sell']-1.0)*100.0
                z['pair']=pair
                z['done']=True
            except:
                z['pair']=pair
                z['done']=False
                

            #put result into out queue
            self.queue_out.put(z)
            


class ThreadOrders(threading.Thread):
    def __init__(self, queue_inp, queue_out):
        threading.Thread.__init__(self)
        self.queue_inp=queue_inp
        self.queue_out=queue_out

    def run(self):
        z={}
        while True:
            task=self.queue_inp.get()
            
            try:
                if BTC_key == '' or BTC_secret == '':
                    raise
                
                nonce = int(int(time.time()*10)%(10*60*60*24*366*10)-867780726+26000000)*2

                # method name and nonce go into the POST parameters
                params = {"method":"OrderList",
                          "nonce": nonce}
                params = urllib.urlencode(params)

                # Hash the params string to produce the Sign header value
                H = hmac.new(BTC_secret, digestmod=hashlib.sha512)
                H.update(params)
                sign = H.hexdigest()

                headers = {"Content-type": "application/x-www-form-urlencoded",
                                   "Key":BTC_key,
                                   "Sign":sign}
                conn = httplib.HTTPSConnection("btc-e.com")
                conn.request("POST", "/tapi", params, headers)
                response = conn.getresponse()
                if response.status != 200:
                    conn.close()
                    raise

                z = json.load(response)
                if z['success'] != 1:
                    conn.close()
                    raise

                conn.close()
                z['done']=True
                
            except:
                z['done']=False
                
            #put result into out queue
            self.queue_out.put(z)

def cancel_order(ord):
    
    nonce = int(int(time.time()*10)%(10*60*60*24*366*10)-867780726+26000000)*2+1

    # method name and nonce go into the POST parameters
    params = {"method":"CancelOrder",
              "nonce": nonce,
              "order_id": ord}
    params = urllib.urlencode(params)

    # Hash the params string to produce the Sign header value
    H = hmac.new(BTC_secret, digestmod=hashlib.sha512)
    H.update(params)
    sign = H.hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
                       "Key":BTC_key,
                       "Sign":sign}
    conn = httplib.HTTPSConnection("btc-e.com")
    conn.request("POST", "/tapi", params, headers)
    response = conn.getresponse()
    if response.status != 200:
        conn.close()
        raise

    a = json.load(response)
    conn.close()
    return a




def trade(ord_type, ord_rate, ord_amount, p):
    
    nonce = int(int(time.time()*10)%(10*60*60*24*366*10)-867780726+26000000)*2+1

    # method name and nonce go into the POST parameters
    params = {"method":"Trade",
              "nonce": nonce,
              "pair": p,
              "type": ord_type,
              "rate": ord_rate,
              "amount": ord_amount}
    params = urllib.urlencode(params)

    # Hash the params string to produce the Sign header value
    H = hmac.new(BTC_secret, digestmod=hashlib.sha512)
    H.update(params)
    sign = H.hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
                       "Key":BTC_key,
                       "Sign":sign}
    conn = httplib.HTTPSConnection("btc-e.com")
    conn.request("POST", "/tapi", params, headers)
    response = conn.getresponse()

    a = json.load(response)

    conn.close()
    return a

   

def get_fg(p, n):
    x=tick_now[p][n]
    y=tick_old[p][n]
    if x>y:
        return 'darkgreen'
    
    if x<y:
        return 'darkred'
    
    return 'black'



def get_ticker(pair):
    url='https://btc-e.com/api/2/'+pair+'/ticker'
    req = urllib2.Request(url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    x=f.read()
    y=json.loads(x)

    z=y['ticker']
    return z




def main():

    def on_close():
        print 'Destroy...'
        root.destroy()
        
    root = Tk()

   
    root.wm_title('BTC-E Trader v.1.0.9 beta')
    root.geometry('1200x700')
    app = App(root)
    
    root.protocol("WM_DELETE_WINDOW", on_close)

    for i in range(len(prs)):
        tr=ThreadTick(queue_inp, queue_out)
        tr.setDaemon(True)
        tr.start()

    for pair in prs:
        queue_inp.put(pair)

    tr2=ThreadOrders(queue_ord_i, queue_ord_o)
    tr2.setDaemon(True)
    tr2.start()
    queue_ord_i.put('go')

    
    
    root.mainloop()
    #root.destroy()


if __name__ == "__main__":
    main()
    
