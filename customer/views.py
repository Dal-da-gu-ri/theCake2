from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
# Create your views here.
from django.views import View

from baker.create_password import passwordMaker
from baker.textBaker import passwordMessage
from home.tokens import account_activation_token
from .textCustomer import messageSend
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes,force_text
from django.views.decorators.csrf import csrf_exempt
from baker.forms import *
from customer.forms import *
from .mappingdate import mappingDate, amountChange
from .ordernum import makeordernum, now
from .secureID import secureID
import requests
from django.views.decorators.csrf import csrf_protect

def join(request):
    res_data = {}

    if request.method == "GET":
        customerform = OrdererForm()
        res_data['customer'] = customerform

        return render(request, 'customer/join_customer.html', res_data)
    elif request.method == "POST":
        customerform = OrdererForm(request.POST)
        if customerform.is_valid():  # 유효성 검사

            try:
                curCustomer = checkOrderer.objects.get(userid=customerform.cleaned_data['userID'])
                try:
                    newCustomer = Orderer.objects.get(userID = customerform.cleaned_data['userID'])
                    res_data['error'] = "이미 가입된 계정입니다."
                    return render(request, 'customer/join_customer.html', res_data)

                except Orderer.DoesNotExist:

                    customerobject = Orderer(
                        userID = customerform.cleaned_data['userID'],
                        email = request.POST.get('email_customer',None),
                        name = customerform.cleaned_data['name'],
                        phoneNum = customerform.cleaned_data['phoneNum'],
                        password = make_password(request.POST.get('password_customer',None))
                    )

                    customerobject.save()
                    current_site = get_current_site(request)
                    message = messageSend("thecake2.ga",
                                          urlsafe_base64_encode(force_bytes(customerobject.pk)).encode().decode(),
                                          account_activation_token.make_token(customerobject))
                    mail_subject = "[The Cake] 회원가입 인증 메일입니다."
                    user_email = customerobject.email
                    email = EmailMessage(mail_subject, message, to=[user_email])
                    email.send()
                    res_data['email'] = user_email
                    return render(request, 'customer/userEmailSent.html', res_data)

            except checkOrderer.DoesNotExist:
                res_data['error'] = "등록되지 않은 아이디입니다."
                return render(request, 'customer/join_customer.html', res_data)
        else:
            return redirect('/customer/inappropriateApproach')

def useridCheck(request):
    if request.method == "GET":  # url을 이용한 방법
        return render(request, 'customer/useridCheck.html')
    elif request.method == "POST":  # 등록 버튼을 사용한 방법기
        userID = request.POST.get('ID_customer',None)
        res_data = {}

        try:
            customer = checkOrderer.objects.get(userid = userID)
            res_data['error'] = "이미 등록된 아이디입니다. 다른 아이디를 입력해주세요!"
            return render(request, 'customer/useridCheck.html', res_data)
        except checkOrderer.DoesNotExist:
            checkorderer = checkOrderer(
                userid=userID
            )
            checkorderer.save()
            return redirect('/customer/signUp/join')

def activate(request,uid64, token):
    res_data = {}
    uid = force_text(urlsafe_base64_decode(uid64))
    customer = Orderer.objects.get(pk=uid)

    if customer is not None and account_activation_token.check_token(customer,token):
        customer.is_active = True
        customer.save()
        if request.method == "GET":
            res_data['customerid'] = customer.userID
            return render(request,'customer/userActivate.html',res_data)
    elif request.method == "POST":
        return redirect('/customer/login')
    else:
        return redirect('/customer/inappropriateApproach')

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
                    return redirect('/customer/main')
                else:
                    res_data['error'] = "아이디/비밀번호 오류"
                    return render(request, 'customer/login_customer.html', res_data)
            else:
                res_data['error'] = "계정을 활성화해주세요."
                return render(request, 'customer/login_customer.html', res_data)
        else:
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
            return render(request, 'customer/main_customer.html',res_data)
        elif request.method == 'POST':
            request.session['sido'] = request.POST.get('sido', None)
            request.session['sigungu'] = request.POST.get('sigungu', None)
            request.session['dong'] = request.POST.get('dong', None)
            return redirect('/customer/main/stores', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/customer/login')


def showStores(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:

        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name

        sido = request.GET['sido']
        sigugun = request.GET['sigugun']
        dong = request.GET['dong']
        day = request.GET['date']
        res_data = {'sido': sido, 'sigugun': sigugun, 'dong': dong, 'date': day}
        orderdate = request.GET['date']
        store_list=[]
        isStore = False

        review_list = Review.objects.all().order_by('cakeName')
        res_data['review_list'] = review_list

        if day:
            orderyear = int(orderdate[0])*1000+int(orderdate[1])*100+int(orderdate[2])*10+int(orderdate[3])
            ordermonth = int(orderdate[5]) * 10 + int(orderdate[6])
            orderday = int(orderdate[8]) * 10 + int(orderdate[9])
            request.session['selectedYear'] = orderyear
            request.session['selectedMonth'] = ordermonth
            request.session['selectedDay'] = orderday

            if sido:
                if sigugun:
                    if dong:
                        stores = Store.objects.filter(daum_sido=sido, daum_sigungu=sigugun, daum_dong=dong)
                        for store in stores:
                            if mappingDate(store,ordermonth,orderday) ==True: # 주문가능한 수량이 있을경우
                                storeobject = Store.objects.get(businessID = store)
                                store_list.append(storeobject)
                                isStore = True

                        if isStore == True:
                            res_data['happy'] = "조회된 가게 있음."
                        else:
                            res_data['error'] = "조회된 가게가 없습니다."

                    else:
                        stores = Store.objects.filter(daum_sido=sido, daum_sigungu=sigugun)
                        for store in stores:
                            if mappingDate(store,ordermonth,orderday) ==True: # 주문가능한 수량이 있을경우
                                storeobject = Store.objects.get(businessID = store)
                                store_list.append(storeobject)
                                isStore = True

                        if isStore == True:
                            res_data['happy'] = "조회된 가게 있음."
                        else:
                            res_data['error'] = "조회된 가게가 없습니다."

                else:
                    stores = Store.objects.filter(daum_sido=sido)
                    for store in stores:
                        if mappingDate(store, ordermonth, orderday) == True:  # 주문가능한 수량이 있을경우
                            storeobject = Store.objects.get(businessID=store)
                            store_list.append(storeobject)
                            isStore = True

                    if isStore==True:
                        res_data['happy']="조회된 가게 있음."
                    else:
                        res_data['error'] = "조회된 가게가 없습니다."

            else:
                res_data['error'] = "픽업 위치를 선택해주세요."

        else:             #선택된 가게가 없는 데 넘어온 경우..
            res_data['error'] = "날짜를 선택해주세요."

        res_data['store_list'] = store_list

        return render(request, 'customer/stores.html', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/customer/login')

def storeInfo(request,pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        storeobject = get_object_or_404(Store,pk=pk)

        if request.method == "GET":
            storeform = StoreForm(instance=storeobject)
            res_data['store'] = storeform

            store_list = Store.objects.filter(pk=pk)
            res_data['store_list'] = store_list
            cake_list = Cake.objects.filter(crn=storeobject.businessID)
            res_data['cake_list'] = cake_list
            res_data['selectedYear']=request.session.get('selectedYear')
            res_data['selectedMonth']=request.session.get('selectedMonth')
            res_data['selectedDay']=request.session.get('selectedDay')
            return render(request,'customer/showCakes.html',res_data)


    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/customer/login')

def showReview(request, pk):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        if request.method == "GET":
            store = Store.objects.get(businessID = pk)
            review_list = Review.objects.filter(storeInfo=pk).order_by('cakeName')
            res_data['store']=store
            res_data['review_list'] = review_list
            return render(request, 'customer/showReview.html', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')




def cakeOrder(request,crn,cakepk):
    res_data = {}
    user_id = request.session.get('user')
    TIME_CHOICES = [
        ('0', '9:00'), ('1', '9:30'), ('2', '10:00'), ('3', '10:30'), ('4', '11:00'),
        ('5', '11:30'),
        ('6', '12:00'), ('7', '12:30'), ('8', '13:00'), ('9', '13:30'), ('10', '14:00'),
        ('11', '14:30'),
        ('12', '15:00'), ('13', '15:30'), ('14', '16:00'), ('15', '16:30'), ('16', '17:00'),
        ('17', '17:30'),
        ('18', '18:00'), ('19', '18:30'), ('20', '19:00'), ('21', '19:30'), ('22', '20:00'),
        ('23', '20:30'),
        ('24', '21:00'), ('25', '21:30'), ('26', '22:00'), ('27', '22:30'),
    ]

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name

        cakeobject = get_object_or_404(Cake,pk=cakepk)
        storeobject = get_object_or_404(Store,businessID=crn)
        pickuptimes = []
        for i in range(int(storeobject.pickUpOpen),int(storeobject.pickUpClose)+1):
            pickuptimes.append(TIME_CHOICES[i][1])
        # print(pickuptimes)
        res_data['selectedYear'] = request.session.get('selectedYear')
        res_data['selectedMonth'] = request.session.get('selectedMonth')
        res_data['selectedDay'] = request.session.get('selectedDay')

        res_data['pickuptimes'] = pickuptimes
        res_data['store']=storeobject
        res_data['cake']=cakeobject

        if request.method == "GET":
            optionspk =[]
            options =[]
            details = []
            option_list = CakeOption.objects.filter(businessID=crn,cakeID=cakepk,isSelected=1)
            detailed_list = DetailedOption.objects.filter(businessID=crn)

            for option in option_list:
                optionspk.append(option.optionID)

            for i in range(0,len(optionspk)):
                optionobject = Option.objects.get(businessID=crn, pk=optionspk[i])
                options.append(optionobject)
                for j in range(0,len(detailed_list)):
                    if detailed_list[j].option_id == optionobject.pk:
                        details.append(detailed_list[j])

            orderoptionform = OrderOptionForm()
            res_data['options']=options
            res_data['detailedOptions'] = details
            res_data['orderoption']= orderoptionform
            return render(request, 'customer/orderCake.html', res_data)
        else:
            # 주문하기 버튼을 눌렀을 때 나올 화면
            if mappingDate(crn,request.session.get('selectedMonth'),request.session.get('selectedDay')) == True:
                orderoptionform = OrderOptionForm(request.POST, request.FILES)
                order = Order(
                    orderNum = makeordernum(),
                    orderer = customer.userID,
                    pickupDate = str(request.session.get('selectedYear'))+"-"+str(request.session.get('selectedMonth'))+"-"+str(request.session.get('selectedDay')),
                    pickupTime = request.POST.get('pickupTime',None),
                    businessID = crn,
                    storeName = storeobject.storeName,
                    location = storeobject.location,
                    storeContact = storeobject.storeContact,
                    cakeName = cakeobject.cakeName,
                    cakeImg = cakeobject.cakeImg,
                    cakeText = request.POST.get('cakeText',None),
                    message = request.POST.get('message',None),
                    price = request.POST.get('total_price',None),
                    status = 0
                )
                order.save()

                options = request.POST.getlist('option', None)
                details = request.POST.getlist('option_detail', None)

                for i in range(0,len(options)):
                    if options[i]:

                        curdetail = DetailedOption.objects.get(businessID=crn,pk=options[i])
                        curoption = Option.objects.get(businessID=crn,optionName=curdetail.option)
                        if curoption.withColorOrImage == '색상판':
                            orderoption = OrderOption(
                                            businessID = crn,
                                            orderer = customer.userID,
                                            optionID = curdetail.pk,
                                            orderID = order.orderNum,
                                            color = details[i]
                                        )
                            orderoption.save()
                        elif curoption.withColorOrImage == '이미지':
                            if orderoptionform.is_valid():
                                orderoption = orderoptionform.save(commit=False)
                                orderoption.businessID = crn
                                orderoption.orderer = customer.userID
                                orderoption.optionID = curdetail.pk
                                orderoption.orderID = order.orderNum
                                orderoption.image = orderoptionform.cleaned_data['image']
                                orderoption.save()
                            else:
                                print(orderoptionform.errors)
                                return redirect('/customer/inappropriateApproach')
                        elif curoption.withColorOrImage == '선택 없음':
                            orderoption = OrderOption(
                                            businessID = crn,
                                            orderer = customer.userID,
                                            optionID = curdetail.pk,
                                            orderID = order.orderNum,
                                        )
                            orderoption.save()

                amountChange(crn, request.session.get('selectedDay'), -1)

                return redirect('/customer/orderList/', res_data)

            else:
                res_data['error']="해당 일자에 주문 가능 수량이 없습니다."
                return redirect('/customer/main/',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')
    #   주문화면

def order_delete(request,pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        orderobject = get_object_or_404(Order, pk=pk)
        pickupdate = orderobject.pickupDate
        orderdate = int(pickupdate[8])*10+int(pickupdate[9])
        amountChange(orderobject.businessID,orderdate,1)
        orderobject.delete()

        if OrderOption.objects.filter(orderID=pk):
            orderoptionobject = OrderOption.objects.filter(orderID=pk)
            orderoptionobject.delete()
        return redirect('/customer/orderList', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def orderlist(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name

        if request.method == "GET":
            order_list = Order.objects.filter(orderer = customer.userID).order_by('-status','pickupDate','pickupTime')
            optionlist = OrderOption.objects.filter(orderID=customer.userID)
            store_list = Store.objects.all()
            res_data['option_list']=optionlist
            res_data['order_list']=order_list
            res_data['store_list'] = store_list
            return render(request, 'customer/orderlist_customer.html',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def cakePay(request,orderNum):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        order = Order.objects.get(orderer=customer.userID, orderNum=orderNum)

        current_site = get_current_site(request)
        res_data['domain']=current_site.domain
        if request.method == "GET":
            res_data['customer']=customer
            res_data['order'] = order
            # order.status = 3
            # order.save()
            return render(request,'customer/pay.html',res_data)
        elif request.method == "POST":
            return render(request, 'customer/paySuccess.html', res_data)


    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

@csrf_protect
def paySuccess(request,orderNum):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        order = Order.objects.get(orderer=customer.userID, orderNum=orderNum)
        optionlist = OrderOption.objects.filter(businessID=order.businessID, orderID=orderNum)
        option_list = []
        for i in range(0, len(optionlist)):
            option = DetailedOption.objects.get(businessID=order.businessID, pk=optionlist[i].optionID)
            option_list.append(option)

        orderoption_list = OrderOption.objects.filter(businessID=order.businessID,orderer=customer.userID,orderID=orderNum)

        res_data['option_list']=option_list
        res_data['orderoption_list']=orderoption_list

        order.status = 3
        order.save()
        if request.method == "GET":
            date = now()
            res_data['date'] = date
            res_data['customer'] = customer
            res_data['order'] = order
            # order.status = 3
            # order.save()
            print(date)

            return render(request, 'customer/paySuccess.html', res_data)
        elif request.method == "POST":
            return render(request, 'customer/paySuccess.html', res_data)
    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

# @csrf_exempt
# def payComplete(request):
#     res_data = {}
#     user_id = request.session.get('user')
#
#     if user_id:
#         customer = Orderer.objects.get(pk=user_id)
#         res_data['customername'] = customer.name
#
#         if request.method == 'POST' and request.is_ajax():
#
#             imp_uid = request.POST.get('imp_uid')
#             # // 액세스 토큰(access token) 발급받기
#             data = {
#                 "imp_key": "5636942716287240",
#                 "imp_secret": "bNleU6QtK96HzjrIWEzGS0MQ353OUmc69yk4FaxpjE6TXyCUdcA5cmWfsZ4mlgtvPNzuY7ThL0bJzNEM"
#             }
#             response = requests.post('https://api.iamport.kr/users/getToken', data=data)
#             data = response.json()
#             my_token = data['response']['access_token']
#
#             #  // imp_uid로 아임포트 서버에서 결제 정보 조회
#             headers = {"Authorization": my_token}
#             response = requests.get('https://api.iamport.kr/payments/' + imp_uid, data=data, headers=headers)
#             data = response.json()
#
#             # // DB에서 결제되어야 하는 금액 조회 const
#             order_amount = 100
#             amountToBePaid = data['response']['amount']  # 아임포트에서 결제후 실제 결제라고 인지 된 금액
#             status = data['response']['status']  # 아임포트에서의 상태
#             if order_amount == amountToBePaid:
#                 # DB에 결제 정보 저장
#                 # await Orders.findByIdAndUpdate(merchant_uid, { $set: paymentData}); // DB에
#                 # if status == 'ready':
#                 #     # DB에 가상계좌 발급정보 저장
#                 #
#                 #     return HttpResponse(json.dumps({'status': "vbankIssued", 'message': "가상계좌 발급 성공"}),
#                 #
#                 #                         content_type="application/json")
#
#                 if status == 'paid':
#                     return render(request, 'customer/paySuccess.html', res_data)
#                     # return HttpResponse(json.dumps({'status': "success", 'message': "일반 결제 성공"}),
#                     #
#                     #                     content_type="application/json")
#                     #
#                 else:
#                     pass
#
#             else:
#                 return render(request, 'customer/inappropriateApproach.html', res_data)
#                 # return HttpResponse(json.dumps({'status': "forgery", 'message': "위조된 결제시도"}),
#                 #                     content_type="application/json")
#         else:
#             return render(request, 'customer/paySuccess.html', res_data)
#     else:
#         if request.method == "GET":
#             res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
#             return render(request, 'customer/inappropriateApproach.html', res_data)
#         elif request.method == "POST":
#             return redirect('/')

def writeReview(request,orderNum):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        reviewobject = Review()
        order = Order.objects.get(orderer=customer.userID, orderNum=orderNum)
        store = Store.objects.get(businessID=order.businessID)

        if request.method == "GET":
            res_data['order'] = order
            return render(request, 'customer/writeReview.html', res_data)
        elif request.method == "POST":
            order.status = 5
            order.save()

            review = Review(
                orderNum = orderNum,
                orderer = customer.userID,
                storeInfo = order.businessID,
                cakeName = order.cakeName,
                textReview = request.POST.get('review', None),

            )

            taste = request.POST.get('taste_rate',None)
            service = request.POST.get('service_rate', None)
            design = request.POST.get('design_rate', None)
            review.taste = int(taste)
            review.service = int(service)
            review.design = int(design)
            review.save()
            avg = request.POST.get('avg_rate', None)
            reviewAvg = float(avg)

            print(store.totalorder,store.totalrate,reviewAvg)
            if store.totalrate != 0 and store.totalorder != 0:
                totalamount = store.totalrate * float(store.totalorder)
            else:
                totalamount = 0
            store.totalrate = (float(totalamount) + reviewAvg) / (float(store.totalorder) +1)
            store.totalorder = store.totalorder + 1

            store.save()
            secureID(customer.userID,orderNum)
            return redirect('/customer/orderList/',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def checkPw(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        if request.method == "GET":
            return render(request, 'customer/checkPw.html',res_data)
        elif request.method == "POST":
            if check_password(request.POST.get('password_customer'), customer.password):
                return redirect('/customer/myPage/editMyInfo/changePw',res_data)
            else:
                res_data['result'] = "비밀번호가 틀렸습니다."
                print(res_data)
                return render(request,'customer/checkPw.html',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def changePw(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        if request.method == "GET":
            res_data = {'userID': customer.userID,
                        'email_customer': customer.email,
                        'phoneNum_customer': customer.phoneNum,
                        'customername': customer.name
                        }
            return render(request, 'customer/changePw.html',res_data)
        elif request.method == "POST":
            newpassword = request.POST.get('password_customer')
            customer.password=make_password(newpassword)
            customer.save()
            res_data = {'userID': customer.userID,
                        'email_customer': customer.email,
                        'phoneNum_customer': customer.phoneNum,
                        'customername': customer.name
                        }
            return redirect('/customer/myPage/editMyInfo/checkPw', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def deleteAccount(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name
        if request.method == "GET":
            return render(request, 'customer/deleteAccount.html',res_data)
        elif request.method == "POST":
            password = request.POST.get('password_customer')
            if check_password(password, customer.password):
                orderrequests = Order.objects.filter(orderer=customer.userID, status=0)
                orderaccept = Order.objects.filter(orderer=customer.userID, status=1)
                orderpaid = Order.objects.filter(orderer=customer.userID, status=3)

                if orderrequests:
                    res_data['result'] = "주문 요청 상태인 주문이 남아있습니다."
                    return redirect('/customer/myPage/deleteAccount',res_data)
                else:
                    if orderaccept:
                        res_data['result'] = "주문 수락 상태인 주문이 남아있습니다."
                        return redirect('/customer/myPage/deleteAccount', res_data)
                    else:
                        if orderpaid:
                            res_data['result'] = "결제 완료 상태인 주문이 남아있습니다."
                            return redirect('/customer/myPage/deleteAccount', res_data)
                        else:
                            res_data['result'] = "진짜.. 탈퇴하실 거예요..? 모든 정보가 삭제돼요..."
                            return render(request,'customer/deleteAccount.html',res_data)
            else:
                res_data['result'] = "비밀번호가 틀렸습니다."
                return render(request,'customer/deleteAccount.html',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def bye(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        customer = Orderer.objects.get(pk=user_id)
        res_data['customername'] = customer.name

        reviewlist = Review.objects.filter(orderer=customer.userID)
        orderoptions = OrderOption.objects.filter(orderer=customer.userID)
        orderlist = Order.objects.filter(orderer=customer.userID)
        checkorderer = checkOrderer.objects.get(userid=customer.userID)
        orderer = Orderer.objects.get(userID=customer.userID)
        for review in reviewlist:
            review.delete()
        for orderoption in orderoptions:
            orderoption.delete()
        for order in orderlist:
            order.delete()
        checkorderer.delete()
        orderer.delete()
        return redirect('/',res_data)


    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def search(request):
    return render(request, 'customer/idpw_search_customer.html')

def idsearch(request):
    if request.method=="GET":
        return render(request,'customer/idpw_search_customer.html')
    elif request.method == "POST":
        #전송받은 이메일 비밀번호 확인
        email = request.POST.get('email_customer')
        res_data={}
        if Orderer.objects.filter(email=email).exists():
            customer = Orderer.objects.get(email=email)
            res_data['result']="고객님의 아이디는 "+customer.userID+" 입니다."
            return render(request, 'customer/idpw_search_customer.html',res_data)
        else:
            res_data['result'] = "등록되지 않은 이메일입니다."
            return render(request, 'customer/idpw_search_customer.html',res_data)

def pwsearch(request):
        userid = request.POST.get('userid')
        res_data = {}
        if Orderer.objects.filter(userID=userid).exists():
            customer = Orderer.objects.get(userID=userid)
            temppw = passwordMaker()
            current_site = get_current_site(request)
            message = passwordMessage(current_site.domain,userid,temppw)
            customer.password = make_password(temppw)
            customer.save()
            mail_subject = "[The Cake] 임시 비밀번호 전송"
            user_email = customer.email
            email = EmailMessage(mail_subject, message, to=[user_email])
            email.send()
            res_data['comment'] = user_email + " 로 임시 비밀번호가 전송되었습니다."
            return render(request, 'customer/idpw_search_customer.html',res_data)

        else:
            res_data['comment'] = "등록되지 않은 아이디입니다."
            return render(request, 'customer/idpw_search_customer.html',res_data)

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