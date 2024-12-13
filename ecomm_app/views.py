from django.shortcuts import render,HttpResponse,redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login, logout
from .models import Product, Cart, Order
from django.db.models import Q
import random
import razorpay
from django.core.mail import send_mail

# Create your views here.

def about(request):
    return HttpResponse("This is about page")

def contact(request):
    return HttpResponse("This is contact page")

def delete(request,rid):
    print("ID to be deleted:",rid)
    return HttpResponse("Id to be deleted: "+rid)

def addition(request,x,y): #x='2',y='4'
    a=int(x)+int(y)
    #print("Addition is:",a)
    return HttpResponse("Addition is:"+ str(a))

class SimpleView(View):
    def get(self,request):
        return HttpResponse("Hello from class view!!")
    
def hello(request):
    context={}
    context['greet']="Good morning, we are learning DTL"
    context['x']=120
    context['y']=100
    context['l']=[10,20,30,40,50,60]
    context['products']=[
        {'id':1,'name':'samsung','cat':'mobile','price':15000},
        {'id':2,'name':'jeans','cat':'clothes','price':800},
        {'id':3,'name':'adidas','cat':'shoes','price':2200},
        {'id':4,'name':'vivo','cat':'mobile','price':16000},
        ]
    return render(request,'hello.html',context)

# estore project-----------------------
def home(request):
    #userid=request.user.id    #3
    #print("logged in userid:",userid)
    # print(request.user.is_authenticated)
    context={}
    p=Product.objects.filter(is_active=True) # 5 objects
    print(p)
    context['products']=p
    return render(request,'index.html',context)

def product_details(request):
    return render(request,'product_details.html')

def register(request):
    if request.method=='POST':
        uname=request.POST['uname'] #""
        upass=request.POST['upass'] #1234
        ucpass=request.POST['ucpass'] #1234
        context={}
        if uname=="" or upass=="" or ucpass=="":
            context['errmsg']="Fields cannot be empty"
        elif upass != ucpass:   
            context['errmsg']="password and confirm password didn't matched!!"
        else:
            try:
                u=User.objects.create(password=upass,username=uname,email=uname)
                u.set_password(upass)
                u.save()
                context['success']="User Created successfully"
            except Exception:
                context['errmsg']="User with same Username already exist!!"
        return render(request,'register.html',context)
        
    else:
        return render(request,'register.html')
    
def user_login(request):
    if request.method=='POST':
        uname=request.POST['uname'] 
        upass=request.POST['upass']
        context={}
        if uname=="" or upass=="":
            context['errmsg']="Fields cannot be empty"
            return render(request,'login.html',context)
        else:
            u=authenticate(username=uname,password=upass)
            if u is not None:
                login(request,u)    #session start
                return redirect('/')    #home page
            else:
                context['errmsg']="Invalid Username & Password"
                return render(request,'login.html',context)
    else:
        return render(request,'login.html')
    
def user_logout(request):
    logout(request)
    return redirect('/')

def catfilter(request,cv):
    q1=Q(is_active=True)
    q2=Q(cat=cv)
    p=Product.objects.filter(q1 & q2)
    print(p)   #2 objects
    context={}
    context['products']=p
    return render(request,'index.html',context)

def sort(request,sv):
    if sv == '0':
        col='price'
    else:
        col='-price'
    p=Product.objects.filter(is_active=True).order_by(col)
    context={}
    context['products']=p
    return render(request,'index.html',context)

def range(request):
    min=request.GET['min']
    max=request.GET['max']
    q1=Q(price__gte=min)
    q2=Q(price__lte=max)
    q3=Q(is_active=True)
    p=Product.objects.filter(q1 & q2 & q3)
    context={}
    context['products']=p
    return render(request,'index.html',context)

def product_details(request,pid):
    p=Product.objects.filter(id=pid)  #id=4=> [<object 4>]
    context={}
    context['products']=p
    return render(request,'product_details.html',context)


def addtocart(request,pid):
    if request.user.is_authenticated:
        userid=request.user.id
        u=User.objects.get(id=userid) # user object (3)
        p=Product.objects.get(id=pid)  #product object(6)
        #check product exist or not
        q1=Q(uid=u)
        q2=Q(pid=p)
        c=Cart.objects.filter(q1 & q2)   #[<cart object 2>]
        # print(c) 
        n=len(c)    #1
        context={}
        if n==1:
            context['errmsg']="Product Already Exists in Cart!!!"
        else:
            c=Cart.objects.create(uid=u,pid=p)
            c.save()
            context['success']="Product Added Successfully"
        p=Product.objects.filter(id=pid)  #id=4=> [<object 4>]
        context['products']=p
        return render(request,'product_details.html',context)
    else:
        return redirect('/login')
    
def viewcart(request):
    c=Cart.objects.filter(uid=request.user.id)  #uid=8 fifthuser
    #print(c)   # 2objects
    s=0
    for x in c:
        # print(x.pid.price)
        s=s+x.pid.price* x.qty
    np=len(c)
    context={}
    context['total']=s
    context['n']=np
    context['data']=c
    return render(request,'cart.html',context)

def remove(request,cid):   #1
    c=Cart.objects.filter(id=cid)    #id=1
    c.delete()
    return redirect('/viewcart')

def updateqty(request,qv,cid):
    c=Cart.objects.filter(id=cid)  #5th object
    print(c[0])
    print(c[0].qty)
    if qv == '1':
        t=c[0].qty+1
        c.update(qty=t)
    else:
        if c[0].qty>1:
            t=c[0].qty-1
            c.update(qty=t)
    return redirect('/viewcart')

def placeorder(request):
    userid=request.user.id
    c=Cart.objects.filter(uid=userid)
    # print(c)
    oid=random.randrange(1000,9999)
    print(oid)
    for x in c:  #[object5, object6]
        # print(x)
        o=Order.objects.create(order_id=oid,pid=x.pid,uid=x.uid,qty=x.qty)
        o.save()
        x.delete()
    orders=Order.objects.filter(uid=request.user.id)
    context={}
    context['data']=orders
    np=len(orders)   #2items
    s=0
    for x in orders:
        s=s+x.pid.price * x.qty
    context['total']=s
    context['n']=np
    return render(request,'placeorder.html',context)
    # return HttpResponse("placeorder")

def makepayment(request):
    orders=Order.objects.filter(uid=request.user.id)
    s=0
    for x in orders:   #2 objects
        s=s+x.pid.price * x.qty
        oid=x.order_id
    # print(oid)
    # print(s)
    client = razorpay.Client(auth=("rzp_test_pjmfONoAV5hhRJ", "2qLFlWxOv0vaA1jxWEEHwbcA"))
    data = { "amount": s*100, "currency": "INR", "receipt": oid }
    payment = client.order.create(data=data)
    # print(payment)
    uemail=request.user.email
    # print(uemail)
    context={}
    context['data']=payment
    context['uemail']=uemail
    # return HttpResponse("Success")
    return render(request,'pay.html',context)

def sendusermail(request,uemail):
    msg="Order details are: "
    # uemail=request.user.email - Error
    print(uemail)
    send_mail(
        "Ekart order placed successfullly",
        msg,
        "dhanashreemhase15@gmail.com",
        [uemail],
        fail_silently=False,
    )
    return HttpResponse("Mail sent successfully")