from django.shortcuts import render, redirect, get_object_or_404
from home.models import Orderer, Order, Store, Baker, Review, Option, DetailedOption, Cake, checkOrderer
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth.hashers import make_password, check_password
# Create your views here.
from home.tokens import account_activation_token
from .textCustomer import messageSend
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes,force_text
from django.views.decorators.csrf import csrf_exempt
from baker.forms import CakeForm,StoreForm


def temp(request):
    return render(request, 'customer/showCakes.html')

def showStores2(request):
    search_key1 = request.GET['search_key1']
    search_key2 = request.GET['search_key2']
    search_key3 = request.GET['search_key3']
    search_key4 = request.GET['search_key4']
    context = { 'search_key1':search_key1, 'search_key2':search_key2, 'search_key3':search_key3, 'search_key4':search_key4 }
    print(context)
    return render(request,'customer/showStores2.html',context)

@csrf_exempt
def main(request):
    return render(request, 'customer/main_customer.html')

def join(request):
    #global bsID, emailBaker
    if request.method == "GET":
        return render(request, 'customer/join_customer.html')
    elif request.method == "POST":
        userID = request.POST.get('ID_customer',None)
        namecustomer = request.POST.get('name_customer',None)
        emailcustomer = request.POST.get('email_customer',None)
        passwordcustomer = request.POST.get('password_customer',None)
        phoneNumcustomer = request.POST.get('phoneNum_customer',None)
        res_data = {}
        try:
            curCustomer = checkOrderer.objects.get(userid = userID)
            customerid = curCustomer.userid

            try:
                newCustomer = Orderer.objects.get(userID=customerid)
                res_data['error'] = "이미 가입된 계정입니다."
                return render(request, 'customer/join_customer.html', res_data)
            except Orderer.DoesNotExist:
                customer = Orderer(
                    userID = userID,
                    email = emailcustomer,
                    name = namecustomer,
                    phoneNum = phoneNumcustomer,
                    password = make_password(passwordcustomer)
                )
                customer.save()
                current_site = get_current_site(request)
                message = messageSend(current_site.domain,
                                      urlsafe_base64_encode(force_bytes(customer.pk)).encode().decode(),
                                      account_activation_token.make_token(customer))
                mail_subject = "[The Cake] 회원가입 인증 메일입니다."
                user_email = customer.email
                email = EmailMessage(mail_subject, message, to=[user_email])
                email.send()
                res_data['comment'] = user_email + " 로 이메일이 발송되었습니다. \n\n인증을 완료해주세요 :)"
                return render(request, 'customer/userEmailSent.html', res_data)
                #return redirect('/customer/login')
                #return render(request, 'fuser/login.html')
        except checkOrderer.DoesNotExist:
            # comment = None
            res_data['error'] = "등록되지 않은 아이디입니다."
            return render(request, 'customer/join_customer.html', res_data)

def useridCheck(request):
    #global bsID
    if request.method == "GET":  # url을 이용한 방법
        return render(request, 'customer/useridCheck.html')
    elif request.method == "POST":  # 등록 버튼을 사용한 방법기
        userID = request.POST.get('ID_customer',None)
        userEmail = request.POST.get('email_customer', None)
        res_data = {}

        try:
            customer = checkOrderer.objects.get(userid = userID)
            res_data['error'] = "이미 등록된 아이디입니다."
            return render(request, 'customer/useridCheck.html', res_data)
        except checkOrderer.DoesNotExist:
            #comment = None
            checkorderer = checkOrderer(
                userid=userID,
                useremail=userEmail
            )
            checkorderer.save()
            return redirect('/customer/signUp/join')
                #return render(request, 'baker/join_baker.html')

def activate(request,uid64, token):
    res_data = {}
    uid = force_text(urlsafe_base64_decode(uid64))
    customer = Orderer.objects.get(pk=uid)

    if customer is not None and account_activation_token.check_token(customer,token):
        customer.is_active = True
        customer.save()
        if request.method == "GET":
            res_data['comment'] = customer.userID+"님의 계정이 활성화되었습니다."
            return render(request,'customer/userActivate.html',res_data)
    elif request.method == "POST":
        return redirect('/customer/login')
    else:
        return redirect('/customer/inappropriateApproach')
        #return HttpResponse('비정상적인 접근입니다.')

def wrongApproach(request):
    if request.method == "GET":
        res_data = {}
        res_data['comment'] = "잘못된 접근입니다."
        return render(request, 'customer/inappropriateApproach.html',res_data)
    elif request.method == "POST":
        return redirect('/')

def login(request):
    if request.method=="GET":
        return render(request,'customer/login_customer.html')
    elif request.method == "POST":
        #전송받은 이메일 비밀번호 확인
        userID = request.POST.get('ID_customer')
        password = request.POST.get('password')

        #유효성 처리
        res_data={}
        if Orderer.objects.filter(userID=userID).exists():
            orderer = Orderer.objects.get(userID=userID)
            if orderer.is_active:
                if check_password(password,orderer.password):
                    request.session['user']=orderer.userID

                    #return render(request,'customer/main_customer.html')  ####여기가 안됨
                    return redirect('/customer/main')
                else:
                    #res_data['error'] = "비밀번호가 틀렸습니다."
                    res_data['error'] = "아이디/비밀번호 오류"
                    return render(request, 'customer/login_customer.html', res_data)
            else:
                res_data['error'] = "계정을 활성화해주세요."
                return render(request, 'customer/login_customer.html', res_data)
        else:
            #res_data['error'] = "존재하지 않는 아이디입니다."
            res_data['error'] = "아이디/비밀번호 오류"
            return render(request,'customer/login_customer.html',res_data)


# # login에 성공하면 main_customer.html으로 이동!
def main_customer(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        if request.method == 'GET':
            #print("get")

            return render(request, 'customer/main_customer.html',res_data)
        elif request.method == 'POST':
            request.session['sido'] = request.POST.get('sido', None)
            request.session['sigungu'] = request.POST.get('sigungu', None)
            request.session['dong'] = request.POST.get('dong', None)

            #날짜도 받도록 해야함
            #print(request.session.get('sido'))
            #print("post")
            #return redirect('/customer/stores', res_data)
            #print("sido: "+request.session.get('sido'))
            #print("sigungu: " + request.session.get('sigungu'))
            # if request.session.get('sigungu'):
            #     print("exist")
            # else:
            #     print("not exist")
            #return HttpResponse(request.session.get('sido')+" "+request.session.get('sigungu')+" "+request.session.get('dong'))
            #return HttpResponse(user_id)
            return redirect('/customer/main/stores', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/customer/login')

    #return render(request, 'customer/main_customer.html')


def showStores(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:

        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        # sido = request.session.get('sido')
        # gungu = request.session.get('gungu')
        # dong = request.session.get('dong')

        sido = request.GET['sido']
        sigugun = request.GET['sigugun']
        dong = request.GET['dong']
        date = request.GET['date']
        res_data = {'sido': sido, 'sigugun': sigugun, 'dong': dong,
                   'date': date}
        if sido:

            if sigugun:

                if dong:

                    store_list = Store.objects.filter(daum_sido=sido, daum_sigungu=sigugun, daum_dong=dong)
                    print(store_list)
                else:
                    store_list = Store.objects.filter(daum_sido=sido, daum_sigungu=sigugun)
            else:
                store_list = Store.objects.filter(daum_sido=sido)
        # else:             #선택된 가게가 없는 데 넘어온 경우..
        #     return HttpResponse(user_id)

        res_data['store_list'] = store_list

        # return render(request, 'customer/showStores.html', res_data)
        return render(request, 'customer/stores.html', res_data)
        # return render(request,'customer/showStores2.html',res_data)


    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/customer/login')

    #return render(request,'customer/showStores.html')


def storeInfo(request,pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        storeobject = get_object_or_404(Store,pk=pk)

        if request.method == "GET":
            storeform = StoreForm(instance=storeobject)
            # cakeform = CakeForm()
            res_data['store'] = storeform

            store_list = Store.objects.filter(pk=pk)
            res_data['store_list'] = store_list
            cake_list = Cake.objects.filter(crn=storeobject.businessID)
            res_data['cake_list'] = cake_list

            # return render(request, 'customer/showStores.html', res_data)
            return render(request,'customer/showCakes.html',res_data)
        elif request.method == "POST":
            ## 케이크 가게가 마음에 들어서 주문하러 기
            return render(request,'customer/showCakes.html',res_data)


            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/customer/login')


    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/customer/login')

def cakeOrder(request,pk1):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name

    return render(request, 'customer/orderlist_customer.html', res_data)
    #   주문화면

def testing(request):

    return render(request,'customer/test.html')

def orderlist(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name

    return render(request, 'customer/orderlist_customer.html',res_data)


def mypage(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name

    return render(request, 'customer/mypage_customer.html',res_data)


def logout(request):
    res_data = {}

    if request.method == "GET":
        if request.session['user']:
            user_id = request.session.get('user')
            customer = Orderer.objects.get(pk=user_id)
            del (request.session['user'])
            res_data['comment'] = customer.name + " 님의 계정이 성공적으로 로그아웃되었습니다!"
            return render(request, 'customer/logout_customer.html', res_data)
        else:
            return redirect('/customer/inappropriateApproach')
    elif request.method == "POST":
        return redirect('/')



def wrongApproach(request):
    if request.method == "GET":
        res_data = {}
        res_data['comment'] = "잘못된 접근입니다."
        return render(request, 'customer/inappropriateApproach.html',res_data)
    elif request.method == "POST":
        return redirect('/')