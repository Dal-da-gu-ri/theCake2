from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .crn import Search_CRN
from home.tokens import account_activation_token
from .textBaker import messageSend,passwordMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes,force_text
from .forms import *

from .create_password import passwordMaker
from .createcakepk import newcakepk
from .dailyamounts import setDailyAmounts
from django.http import JsonResponse

from customer.mappingdate import mappingDate, amountChange

def join(request):
    if request.method == "GET":
        return render(request, 'baker/join_baker.html')
    elif request.method == "POST":
        userid = request.POST.get('userid',None)
        namebaker = request.POST.get('name_baker',None)
        emailbaker = request.POST.get('email_baker',None)
        passwordbaker = request.POST.get('password_baker',None)
        phoneNumbaker = request.POST.get('phoneNum_baker',None)
        res_data = {}
        try:
            curBaker = checkBaker.objects.get(userid = userid)
            crnNum = curBaker.businessCRN

            try:
                newBaker = Baker.objects.get(userID=userid)
                res_data['error'] = "이미 가입된 계정입니다."
                return render(request, 'baker/join_baker.html', res_data)
            except Baker.DoesNotExist:

                baker = Baker(
                    businessID=crnNum,
                    userID=userid,
                    email=emailbaker,
                    name=namebaker,
                    phoneNum=phoneNumbaker,
                    password=make_password(passwordbaker)
                )
                baker.save()

                store = Store(
                    businessID = crnNum
                )
                store.save()
                current_site = get_current_site(request)
                message = messageSend(current_site.domain,
                                  urlsafe_base64_encode(force_bytes(baker.pk)).encode().decode(),
                                  account_activation_token.make_token(baker))
                mail_subject = "[The Cake] 회원가입 인증 메일입니다."
                user_email = baker.email
                email = EmailMessage(mail_subject, message, to=[user_email])
                email.send()
                res_data['email'] = user_email
                return render(request,'baker/userEmailSent.html',res_data)
        except checkBaker.DoesNotExist:
            res_data['error'] = "등록되지 않은 아이디입니다."
            return render(request, 'baker/join_baker.html', res_data)


def login(request):
    if request.method=="GET":
        return render(request,'baker/login_baker.html')
    elif request.method == "POST":
        #전송받은 이메일 비밀번호 확인
        userid = request.POST.get('userid')
        password = request.POST.get('password')

        #유효성 처리
        res_data={}
        if Baker.objects.filter(userID=userid).exists():
            baker = Baker.objects.get(userID=userid)
            if baker.is_active:
                if check_password(password,baker.password):
                    request.session['user']=baker.userID
                    return redirect('/baker/manageStore/enrollStore')
                else:
                    res_data['error'] = "아이디/비밀번호 오류"
                    return render(request, 'baker/login_baker.html', res_data)
            else:
                res_data['error'] = "계정을 활성화해주세요."
                return render(request, 'baker/login_baker.html', res_data)

        else:
            res_data['error'] = "아이디/비밀번호 오류"
            return render(request,'baker/login_baker.html',res_data)

def crnCheck(request):
    if request.method == "GET":  # url을 이용한 방법
        return render(request, 'baker/crnCheck.html')
    elif request.method == "POST":  # 등록 버튼을 사용한 방법기
        bakerid = request.POST.get('userid',None)
        crn = request.POST.get('businessID', None)
        res_data = {}
        try:
            baker = checkBaker.objects.get(userid = bakerid)
            res_data['error'] = "이미 등록된 아이디입니다."
            return render(request, 'baker/crnCheck.html', res_data)

        except checkBaker.DoesNotExist:
            if Search_CRN(crn) == "부가가치세 일반과세자 입니다.":
                try:
                    baker = checkBaker.objects.get(businessCRN=crn)
                    res_data['error'] = "이미 등록된 사업자등록번호입니다."
                    return render(request, 'baker/crnCheck.html', res_data)
                except checkBaker.DoesNotExist:
                    checkbaker = checkBaker(
                        userid=bakerid,
                        businessCRN=crn
                    )
                    checkbaker.save()
                    return redirect('/baker/signUp/join')
            else:
                res_data['error'] = "유효하지 않은 사업자등록번호입니다."
                return render(request, 'baker/crnCheck.html', res_data)

def isID(request):
    bakerid = request.POST.get('userid', None)
    res_data = {}
    try:
        baker = Baker.objects.get(userid=bakerid)
        res_data['msg'] = "fail"
        return JsonResponse(res_data)

    except Baker.DoesNotExist:
        res_data['msg'] = "pass"
        return JsonResponse(res_data)

def isEmail(request):
    emailbaker = request.POST.get('email_baker', None)
    res_data = {}
    try:
        baker = Baker.objects.get(email=emailbaker)
        res_data['msg'] = "fail"
        return JsonResponse(res_data)

    except Baker.DoesNotExist:
        res_data['msg'] = "pass"
        return JsonResponse(res_data)

def isCRN(request):
    crn = request.POST.get('businessID', None)
    res_data = {}
    try:
        baker = Baker.objects.get(businessID=crn)
        res_data['msg'] = "fail"
        return JsonResponse(res_data)

    except Baker.DoesNotExist:
        res_data['msg'] = "pass"
        return JsonResponse(res_data)

def activate(request,uid64, token):
    res_data = {}
    uid = force_text(urlsafe_base64_decode(uid64))
    baker = Baker.objects.get(pk=uid)

    if baker is not None and account_activation_token.check_token(baker,token):
        baker.is_active = True
        baker.save()
        if request.method == "GET":
            res_data['bakerid']=baker.userID
            return render(request,'baker/userActivate.html',res_data)
    elif request.method == "POST":
        return redirect('/baker/login')
    else:
        return redirect('/baker/inappropriateApproach')

def wrongApproach(request):
    if request.method == "GET":
        res_data = {}
        res_data['comment'] = "잘못된 접근입니다."
        return render(request, 'baker/inappropriateApproach.html',res_data)
    elif request.method == "POST":
        return redirect('/')

def enrollStore(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        storeobject = Store()
        if request.method == 'POST':
            existance = False
            try:
                storeobject = Store.objects.get(businessID=baker.businessID)
                existance = True
                totalorder = storeobject.totalorder
                totalrate = storeobject.totalrate
            except Store.DoesNotExist:
                storeobject=Store()
            storeform = StoreForm(request.POST, request.FILES)
            if storeform.is_valid(): #유효성 검사
                    storeobject.businessID = baker.businessID
                    storeobject.manager = baker
                    storeobject.storeName = storeform.cleaned_data['storeName']
                    storeobject.storeContact = storeform.cleaned_data['storeContact']
                    storeobject.pickUpOpen = storeform.cleaned_data['pickUpOpen']
                    storeobject.pickUpClose = storeform.cleaned_data['pickUpClose']
                    storeobject.aboutStore = storeform.cleaned_data['aboutStore']
                    storeobject.postcode = storeform.cleaned_data['postcode']
                    storeobject.address1 = storeform.cleaned_data['address1']
                    storeobject.address2 = storeform.cleaned_data['address2']
                    storeobject.address3 = storeform.cleaned_data['address3']

                    if storeform.cleaned_data['address2']:
                        storeobject.location = storeform.cleaned_data['address1'] + " " + storeform.cleaned_data[
                            'address2']
                    else:
                        storeobject.location = storeform.cleaned_data['address1']

                    storeobject.daum_sido = request.POST.get('daum_sido',None)
                    storeobject.daum_sigungu = request.POST.get('daum_sigungu',None)
                    storeobject.daum_dong = request.POST.get('daum_dong',None)
                    storeobject.storeImg = storeform.cleaned_data['storeImg']
                    storeobject.bankname = storeform.cleaned_data['bankname']
                    storeobject.banknumber = storeform.cleaned_data['banknumber']

                    if existance:
                        storeobject.totalorder = totalorder
                        storeobject.totalrate = totalrate
                    else:
                        storeobject.totalorder = 0
                        storeobject.totalrate = 0

                    storeobject.save()
                    res_data['store'] = storeform
                    res_data['name'] = storeobject.storeImg
                    return render(request, 'baker/enrollStore2.html', res_data)
            else:
                    print(storeform.errors)
                    return redirect('/baker/inappropriateApproach')

        else:
            try:
                storeobject = Store.objects.get(businessID=baker.businessID)
                storeform = StoreForm(instance=storeobject)
            except Store.DoesNotExist:
                storeobject=Store()
                storeform = StoreForm(instance=storeobject)
            res_data['store'] = storeform

            return render(request, 'baker/enrollStore2.html', res_data)

    else:
        if request.method == "GET":
            res_data = {}
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def opendays(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        daysobject = OpenDays()
        if request.method == "POST":
            daysform = OpenDaysForm(request.POST)
            if daysform.is_valid():
                daysobject.businessID = baker.businessID
                daysobject.monday = daysform.cleaned_data['monday']
                daysobject.tuesday = daysform.cleaned_data['tuesday']
                daysobject.wednesday = daysform.cleaned_data['wednesday']
                daysobject.thursday = daysform.cleaned_data['thursday']
                daysobject.friday = daysform.cleaned_data['friday']
                daysobject.saturday = daysform.cleaned_data['saturday']
                daysobject.sunday = daysform.cleaned_data['sunday']
                daysobject.save()
                res_data['opendays'] = daysform

                setDailyAmounts(baker.businessID,daysobject.sunday,daysobject.monday,daysobject.tuesday,daysobject.wednesday,
                                daysobject.thursday,daysobject.friday,daysobject.saturday)
                return redirect('/baker/manageStore/weekhandle/', res_data)

            else:
                    return redirect('/baker/inappropriateApproach')

        else:
            try:
                daysobject = OpenDays.objects.get(businessID=baker.businessID)
                daysform = OpenDaysForm(instance=daysobject)
            except OpenDays.DoesNotExist:
                daysobject=OpenDays()
                daysform = OpenDaysForm(instance=daysobject)
            res_data['opendays'] = daysform
            return render(request, 'baker/weekhandle.html', res_data) # 나중에 opendays.html으로 바꿔야함

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def dailyamountsetting(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        # daysobject = OpenDays()
        dailyobject = DailyAmount()
        if request.method == "POST":
            print("heree")
            dailyform = DailyAmountForm(request.POST)
            if dailyform.is_valid():
                dailyobject.businessID = baker.businessID
                dailyobject.day1 = dailyform.cleaned_data['day1']
                dailyobject.day2 = dailyform.cleaned_data['day2']
                dailyobject.day3 = dailyform.cleaned_data['day3']
                dailyobject.day4 = dailyform.cleaned_data['day4']
                dailyobject.day5 = dailyform.cleaned_data['day5']
                dailyobject.day6 = dailyform.cleaned_data['day6']
                dailyobject.day7 = dailyform.cleaned_data['day7']
                dailyobject.day8 = dailyform.cleaned_data['day8']
                dailyobject.day9 = dailyform.cleaned_data['day9']
                dailyobject.day10 = dailyform.cleaned_data['day10']
                dailyobject.day11 = dailyform.cleaned_data['day11']
                dailyobject.day12 = dailyform.cleaned_data['day12']
                dailyobject.day13 = dailyform.cleaned_data['day13']
                dailyobject.day14 = dailyform.cleaned_data['day14']
                dailyobject.day15 = dailyform.cleaned_data['day15']
                dailyobject.day16 = dailyform.cleaned_data['day16']
                dailyobject.day17 = dailyform.cleaned_data['day17']
                dailyobject.day18 = dailyform.cleaned_data['day18']
                dailyobject.day19 = dailyform.cleaned_data['day19']
                dailyobject.day20 = dailyform.cleaned_data['day20']
                dailyobject.day21 = dailyform.cleaned_data['day21']
                dailyobject.day22 = dailyform.cleaned_data['day22']
                dailyobject.day23 = dailyform.cleaned_data['day23']
                dailyobject.day24 = dailyform.cleaned_data['day24']
                dailyobject.day25 = dailyform.cleaned_data['day25']
                dailyobject.day26 = dailyform.cleaned_data['day26']
                dailyobject.day27 = dailyform.cleaned_data['day27']
                dailyobject.day28 = dailyform.cleaned_data['day28']
                dailyobject.day29 = dailyform.cleaned_data['day29']
                dailyobject.day30 = dailyform.cleaned_data['day30']
                dailyobject.day31 = dailyform.cleaned_data['day31']
                # dailyobject.day32 = dailyform.cleaned_data['day32']
                # dailyobject.day33 = dailyform.cleaned_data['day33']
                # dailyobject.day34 = dailyform.cleaned_data['day34']
                # dailyobject.day35 = dailyform.cleaned_data['day35']
                # dailyobject.day36 = dailyform.cleaned_data['day36']
                # dailyobject.day37 = dailyform.cleaned_data['day37']
                # dailyobject.day38 = dailyform.cleaned_data['day38']
                # dailyobject.day39 = dailyform.cleaned_data['day39']
                # dailyobject.day40 = dailyform.cleaned_data['day40']
                # dailyobject.day41 = dailyform.cleaned_data['day41']
                # dailyobject.day42 = dailyform.cleaned_data['day42']
                # dailyobject.day43 = dailyform.cleaned_data['day43']
                # dailyobject.day44 = dailyform.cleaned_data['day44']
                # dailyobject.day45 = dailyform.cleaned_data['day45']
                # dailyobject.day46 = dailyform.cleaned_data['day46']
                # dailyobject.day47 = dailyform.cleaned_data['day47']
                # dailyobject.day48 = dailyform.cleaned_data['day48']
                # dailyobject.day49 = dailyform.cleaned_data['day49']
                # dailyobject.day50 = dailyform.cleaned_data['day50']
                # dailyobject.day51 = dailyform.cleaned_data['day51']
                # dailyobject.day52 = dailyform.cleaned_data['day52']
                # dailyobject.day53 = dailyform.cleaned_data['day53']
                # dailyobject.day54 = dailyform.cleaned_data['day54']
                # dailyobject.day55 = dailyform.cleaned_data['day55']
                # dailyobject.day56 = dailyform.cleaned_data['day56']
                # dailyobject.day57 = dailyform.cleaned_data['day57']
                # dailyobject.day58 = dailyform.cleaned_data['day58']
                # dailyobject.day59 = dailyform.cleaned_data['day59']
                # dailyobject.day60 = dailyform.cleaned_data['day60']
                # dailyobject.day61 = dailyform.cleaned_data['day61']
                # dailyobject.day62 = dailyform.cleaned_data['day62']

                dailyobject.save()
                res_data['dailyform'] = dailyform

                return redirect('/baker/manageStore/datehandle/', res_data)

            else:
                print(dailyform)
                return redirect('/baker/inappropriateApproach')

        else:
            try:
                dailyobject = DailyAmount.objects.get(businessID=baker.businessID)
                dailyform = DailyAmountForm(instance=dailyobject)
            except DailyAmount.DoesNotExist:
                dailyobject=DailyAmount()
                dailyform = DailyAmountForm(instance=dailyobject)
            res_data['dailyform'] = dailyform
            return render(request, 'baker/dayhandle2.html', res_data)  # 나중에 opendays.html으로 바꿔야함

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')


# 케이크 관리
def myCakes(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        cake_list = Cake.objects.filter(crn=baker.businessID)
        res_data['cake_list']= cake_list
        return render(request, 'baker/myCakes.html',res_data)
    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/baker/login')

def cake_add(request):
    res_data = {}
    user_id = request.session.get('user')
    cakesearch = False
    # 전체 옵션들 가져와서 for문 안에서 객체 생성.

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        if request.method == "POST":
            cakeform = CakeForm(request.POST,request.FILES)
            store = Store.objects.get(pk=baker.businessID)

            if cakeform.is_valid():
                cakeobject = cakeform.save(commit=False)
                cakeobject.crn = store.businessID
                cakeobject.cakeName = cakeform.cleaned_data['cakeName']
                cakeobject.cakeImg = cakeform.cleaned_data['cakeImg']
                cakeobject.cakePrice = cakeform.cleaned_data['cakePrice']
                while cakesearch == False:
                    newpk = newcakepk()
                    try:
                        cake = Cake.objects.get(pk=newpk)
                        cakesearch = False
                    except Cake.DoesNotExist:
                        cakesearch = True
                cakeobject.cakeid = str(newpk)
                selectedoptions = request.POST.getlist('option_selected',None)

                option_list = Option.objects.filter(businessID=baker.businessID)
                for option in option_list:
                    cakeoption = CakeOption(
                        businessID=baker.businessID,
                        optionID=option.pk,
                        cakeID=newpk,
                        isSelected=False
                    )
                    cakeoption.save()


                for option in selectedoptions:
                    cakeoption = CakeOption.objects.get(businessID=baker.businessID,optionID=option,cakeID= newpk)
                    cakeoption.isSelected = True
                    cakeoption.save()

                print(selectedoptions)



                if Cake.objects.filter(cakeName=cakeobject.cakeName, crn=cakeobject.crn).exists():
                    cakeform = CakeForm()
                    res_data['cake'] = cakeform
                    options = Option.objects.filter(businessID=baker.businessID)
                    res_data['options'] = options
                    res_data['error'] = "이미 등록된 케이크 이름입니다."
                    return render(request, 'baker/cake_add.html', res_data)
                else:
                    cakeobject.save()
                    res_data['cake'] = cakeform
                    return redirect('/baker/manageCake/myCakes', res_data)
            else:
                    print(cakeform.errors)
                    return redirect('/baker/inappropriateApproach')

        else:
            cakeform = CakeForm()
            options = Option.objects.filter(businessID=baker.businessID)
            res_data['options'] = options
            res_data['cake'] = cakeform
            return render(request, 'baker/cake_add.html', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')


def cake_edit(request,pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        curcake = Cake.objects.get(pk=pk)
        baker = Baker.objects.get(businessID=curcake.crn)
        res_data['bakername'] = baker.name
        cakeobject = get_object_or_404(Cake,pk=pk)

        selOptions=[]
        if request.method == "POST":
            cakeform = CakeForm(request.POST,request.FILES,instance=cakeobject)
            if cakeform.is_valid():

                res_data['cake'] = cakeform
                res_data['name'] = cakeobject.cakeImg

                selectedoptions = request.POST.getlist('option_selected',None)
                alloptions = CakeOption.objects.filter(businessID=baker.businessID,cakeID=pk)

                option_list = Option.objects.filter(businessID=baker.businessID)
                available = False
                for i in range(0,len(option_list)):
                    print("1:",available)
                    for j in range(0,len(alloptions)):
                        if option_list[i].pk == alloptions[j].optionID:
                            available = True

                    if available == False:
                        cakeoption = CakeOption(
                            businessID=baker.businessID,
                            optionID=option_list[i].pk,
                            cakeID=pk,
                            isSelected=False
                        )
                        cakeoption.save()
                    available = False

                alloptions = CakeOption.objects.filter(businessID=baker.businessID,cakeID=pk)
                optionhandle = False
                for opt in alloptions:
                    for sel in range(0,len(selectedoptions)):
                        if opt.optionID == int(selectedoptions[sel]):
                            optionhandle = True
                            opt.isSelected = True
                            opt.save()
                    if optionhandle == False:
                        opt.isSelected = False
                        opt.save()
                    optionhandle = False
                selectedoptions = CakeOption.objects.filter(businessID=baker.businessID,
                                                            cakeID=cakeobject.pk, isSelected=1)
                for opt in selectedoptions:
                    selOptions.append(opt.optionID)
                res_data['selectedoptions'] = selOptions


                if Cake.objects.filter(crn=cakeobject.crn,cakeName=cakeobject.cakeName).exists():

                    thiscake=Cake.objects.filter(crn=cakeobject.crn,cakeName=cakeobject.cakeName)
                    if len(thiscake)>1:
                        cakeform = CakeForm(instance=cakeobject)
                        options = Option.objects.filter(businessID=baker.businessID)

                        res_data['cake'] = cakeform
                        res_data['options'] = options

                        res_data['error'] = "이미 등록된 케이크 이름입니다."
                        return render(request, 'baker/cake_edit.html', res_data)
                    else:
                        thiscake = Cake.objects.get(crn=cakeobject.crn, cakeName=cakeobject.cakeName)
                        if thiscake.cakeid != pk:
                            cakeform = CakeForm(instance=cakeobject)
                            options = Option.objects.filter(businessID=baker.businessID)
                            res_data['cake'] = cakeform
                            res_data['options'] = options
                            res_data['error'] = "이미 등록된 케이크 이름입니다."
                            return render(request, 'baker/cake_edit.html', res_data)
                        else:
                            cakeobject = cakeform.save()
                            cakeobject.save()
                            res_data['cake'] = cakeform
                            return redirect('/baker/manageCake/myCakes', res_data)
                else:
                    cakeobject = cakeform.save()
                    cakeobject.save()
                    res_data['cake'] = cakeform
                    return redirect('/baker/manageCake/myCakes', res_data)
            else:
                    cakeform = CakeForm()
                    res_data['cake'] = cakeform
                    return render(request, 'baker/cake_edit.html', res_data)

        else:
            cakeform = CakeForm(instance=cakeobject)
            options = Option.objects.filter(businessID=baker.businessID)
            selectedoptions = CakeOption.objects.filter(businessID=baker.businessID,cakeID=cakeobject.pk,isSelected=1)
            for opt in selectedoptions:
                selOptions.append(opt.optionID)
            res_data['selectedoptions'] = selOptions
            res_data['cake'] = cakeform
            res_data['options'] = options
            return render(request, 'baker/cake_edit.html', res_data)

    else:
        if request.method == "GET":
            res_data = {}
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')


def cake_delete(request, pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        cakeobject = get_object_or_404(Cake, pk=pk)
        cakeoptions = CakeOption.objects.filter(businessID=baker.businessID,cakeID=cakeobject.pk)
        for opt in cakeoptions:
            opt.delete()
        cakeobject.delete()
        return redirect('/baker/manageCake/myCakes', res_data)
    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def options(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
    return render(request, 'baker/options.html')

#주문관리
def manageOrder(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        order_list = Order.objects.filter(businessID=baker.businessID).order_by('status','pickupDate','pickupTime')
        print(order_list)
        res_data['order_list'] = order_list
        if request.method == "GET":
            return render(request, 'baker/manageOrder.html',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def orderInfo(request, pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name

        order = Order.objects.get(businessID=baker.businessID,orderNum=pk)
        optionlist = OrderOption.objects.filter(businessID=baker.businessID,orderID=pk)
        option_list =[]
        print(order.cakeImg)
        print(len(optionlist))
        print(optionlist[0].optionID)
        for i in range(0,len(optionlist)):
            option = DetailedOption.objects.get(businessID=baker.businessID,pk=optionlist[i].optionID)
            option_list.append(option)

        orderer = Orderer.objects.get(userID=order.orderer)
        orderoption_list = OrderOption.objects.filter(businessID=baker.businessID,orderer=orderer.userID,orderID=pk)

        res_data['orderer']=orderer
        res_data['order'] = order
        res_data['option_list']=option_list
        res_data['orderoption_list']=orderoption_list
        if request.method == "GET":
            return render(request, 'baker/orderInfo.html', res_data)
        elif request.method == "POST":
            order.status = 1
            order.save()
            return redirect('/baker/manageOrder/',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')


def orderReject(request,pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name

        order = Order.objects.get(businessID=baker.businessID,orderNum=pk)


        if request.method == "GET":

            res_data['order'] = order
            return render(request, 'baker/order_reject.html', res_data)
        elif request.method == "POST":
            msg = request.POST.get('fromManager', None)

            pickupdate = order.pickupDate
            orderdate = int(pickupdate[8]) * 10 + int(pickupdate[9])
            amountChange(order.businessID, orderdate, 1)

            order.fromManager = msg
            order.status = 2
            order.save()
            return redirect('/baker/manageOrder', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def mypage(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
    return render(request, 'baker/mypage_baker.html',res_data)

def search(request):
    return render(request, 'baker/idpw_search_baker.html')

def idsearch(request):
    if request.method=="GET":
        return render(request,'baker/idpw_search_baker.html')
    elif request.method == "POST":
        #전송받은 이메일 비밀번호 확인
        email = request.POST.get('email_baker')
        res_data={}
        if Baker.objects.filter(email=email).exists():
            baker = Baker.objects.get(email=email)
            res_data['result']="고객님의 아이디는 "+baker.userID+" 입니다."
            return render(request, 'baker/idpw_search_baker.html',res_data)
        else:
            res_data['result'] = "등록되지 않은 이메일입니다."
            return render(request, 'baker/idpw_search_baker.html',res_data)

def pwsearch(request):
        print("here")
        userid = request.POST.get('userid')
        print(userid)
        res_data = {}
        if Baker.objects.filter(userID=userid).exists():
            baker = Baker.objects.get(userID=userid)
            temppw = passwordMaker()
            current_site = get_current_site(request)
            message = passwordMessage(current_site.domain,userid,temppw)
            baker.password = make_password(temppw)
            baker.save()
            mail_subject = "[The Cake] 임시 비밀번호 전송"
            user_email = baker.email
            email = EmailMessage(mail_subject, message, to=[user_email])
            email.send()
            res_data['comment'] = user_email + " 로 임시 비밀번호가 전송되었습니다."
            return render(request, 'baker/idpw_search_baker.html',res_data)

        else:
            res_data['comment'] = "등록되지 않은 아이디입니다."
            return render(request, 'baker/idpw_search_baker.html',res_data)



def editInfo(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
    return render(request,'baker/changePw.html',res_data)

def checkPw(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        if request.method == "GET":
            return render(request, 'baker/checkPw.html',res_data)
        elif request.method == "POST":
            if check_password(request.POST.get('password_baker'), baker.password):
                return redirect('/baker/myPage/editMyInfo/changePw',res_data)
            else:
                res_data['result'] = "비밀번호가 틀렸습니다."
                print(res_data)
                return render(request,'baker/checkPw.html',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')


def changePw(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        baker = Baker.objects.get(pk=user_id)
        if request.method == "GET":
            res_data = {'userID': baker.userID,
                        'email_baker': baker.email,
                        'phoneNum_baker': baker.phoneNum,
                        'bakername': baker.name
                        }
            return render(request, 'baker/changePw.html',res_data)
        elif request.method == "POST":
            newpassword = request.POST.get('password_baker')
            baker.password=make_password(newpassword)
            baker.save()
            res_data = {'userID': baker.userID,
                        'email_baker': baker.email,
                        'phoneNum_baker': baker.phoneNum,
                        'bakername': baker.name
                        }
            print(res_data)
            return redirect('/baker/myPage/editMyInfo/checkPw', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def deleteAccount(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        if request.method == "GET":
            return render(request, 'baker/deleteAccount.html',res_data)
        elif request.method == "POST":
            password = request.POST.get('password_baker')
            if check_password(password, baker.password):

                orderrequests = Order.objects.filter(businessID=baker.businessID,status=0)
                orderaccept = Order.objects.filter(businessID=baker.businessID,status=1)
                orderpaid = Order.objects.filter(businessID=baker.businessID,status=3)

                if orderrequests:
                    res_data['result'] = "주문 요청 상태인 주문이 남아있습니다."
                    return redirect('/baker/myPage/deleteAccount',res_data)
                else:
                    if orderaccept:
                        res_data['result'] = "주문 수락 상태인 주문이 남아있습니다."
                        return redirect('/baker/myPage/deleteAccount', res_data)
                    else:
                        if orderpaid:
                            res_data['result'] = "결제 완료 상태인 주문이 남아있습니다."
                            return redirect('/baker/myPage/deleteAccount', res_data)
                        else:
                            res_data['result'] = "진짜.. 탈퇴하실 거예요..? 모든 정보가 삭제돼요..."
                            return render(request,'baker/deleteAccount.html',res_data)

            else:
                res_data['result'] = "비밀번호가 틀렸습니다."
                print(res_data)
                return render(request,'baker/deleteAccount.html',res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def bye(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name

        store = Store.objects.get(businessID=baker.businessID)
        reviewlist = Review.objects.filter(storeInfo=baker.businessID)
        orderoptions = OrderOption.objects.filter(businessID=baker.businessID)
        orders = Order.objects.filter(businessID=baker.businessID)
        options = Option.objects.filter(businessID=baker.businessID)
        opendays = OpenDays.objects.get(businessID=baker.businessID)
        detailedoptions = DetailedOption.objects.filter(businessID=baker.businessID)
        dailyamount = DailyAmount.objects.get(businessID=baker.businessID)
        checkbaker = checkBaker.objects.get(businessCRN=baker.businessID)
        cakeoptions = CakeOption.objects.filter(businessID=baker.businessID)
        cakes = Cake.objects.filter(crn=baker.businessID)
        baker = Baker.objects.get(businessID=baker.businessID)

        store.delete()
        for review in reviewlist:
            review.delete()
        for orderoption in orderoptions:
            orderoption.delete()
        for order in orders:
            order.delete()
        for option in options:
            option.delete()
        opendays.delete()
        for detailedoption in detailedoptions:
            detailedoption.delete()
        dailyamount.delete()
        checkbaker.delete()
        for cakeoption in cakeoptions:
            cakeoption.delete()
        for cake in cakes:
            cake.delete()
        baker.delete()

        return redirect('/',res_data)


    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'customer/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')

def logout(request):
    res_data = {}

    if request.method == "GET":
        if request.session['user']:
            user_id = request.session.get('user')
            baker = Baker.objects.get(pk=user_id)
            del (request.session['user'])
            res_data['comment'] = baker.name + " 님의 계정이 성공적으로 로그아웃되었습니다!"
            return render(request, 'baker/logout_baker.html', res_data)
        else:
            return redirect('/baker/inappropriateApproach')
    elif request.method == "POST":
        return redirect('/')


def options(request):
    res_data = {}
    user_id = request.session.get('user')
    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        option_list = Option.objects.filter(businessID=baker.businessID)
        detail_list = DetailedOption.objects.all()

        res_data['option_list']= option_list
        res_data['detail_list']=detail_list
        return render(request, 'baker/options.html',res_data)
    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/baker/login')


def option_add(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name

        if request.method == 'GET':
            optionform = OptionForm(request.GET or None)
            formset = DetailedOptionFormset(queryset=DetailedOption.objects.none())
            res_data['optionform']=optionform
            res_data['formset']=formset
            return render(request, 'baker/option_add.html', res_data)
        elif request.method == 'POST':
            optionform = OptionForm(request.POST)
            formset = DetailedOptionFormset(request.POST)
            if optionform.is_valid() and formset.is_valid():
                option = optionform.save(commit=False)
                option.businessID = baker.businessID
                option.optionName = optionform.cleaned_data['optionName']
                option.isNecessary = optionform.cleaned_data['isNecessary']
                option.withColorOrImage = optionform.cleaned_data['withColorOrImage']
                option = optionform.save()
                option.save()
                for form in formset:
                    detail = form.save(commit=False)
                    detail.option = option
                    detail.businessID = baker.businessID
                    detail.detailName = form.cleaned_data['detailName']
                    detail.pricing = form.cleaned_data['pricing']
                    detail.save()

                return redirect('/baker/manageCake/options/',res_data)
            else:
                print(optionform.errors)
                optionform = OptionForm(request.GET or None)
                formset = DetailedOptionFormset(queryset=DetailedOption.objects.none())
                res_data['optionform'] = optionform
                res_data['formset'] = formset
                res_data['error']="모든 칸을 입력해주세요."
                return render(request, 'baker/option_add.html', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')



def option_edit(request,pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        optionobject = get_object_or_404(Option,pk=pk)
        if DetailedOption.objects.filter(option_id = optionobject.pk,businessID = baker.businessID):
            detail_list = DetailedOption.objects.filter(option_id = optionobject.pk,businessID = baker.businessID)

        if request.method == "POST":
            optionform = OptionForm(request.POST,instance=optionobject)
            formset = DetailedOptionFormset(request.POST,instance=detail_list)

            if optionform.is_valid() and formset.is_valid():

                optionobject = optionform.save()
                optionobject.save()

                for form in formset:
                    detail = form.save()
                    detail.save()

                res_data['option'] = optionform
                res_data['detail'] = detail
                return redirect('/baker/manageCake/options', res_data)
            else:
                    return render(request, 'baker/option_edit.html', res_data)

        else:
            optionform = OptionForm(instance=optionobject)
            if DetailedOption.objects.filter(option_id=optionobject.pk, businessID=baker.businessID):
                detail_list = DetailedOption.objects.filter(option_id=optionobject.pk, businessID=baker.businessID)
            res_data['option'] = optionform
            res_data['detail'] = detail_list
            return render(request, 'baker/option_edit.html', res_data)

    else:
        if request.method == "GET":
            res_data = {}
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')


def option_delete(request,pk):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        optionobject = get_object_or_404(Option, pk=pk)

        if DetailedOption.objects.filter(option_id=optionobject.pk, businessID=baker.businessID):
            detailobject = DetailedOption.objects.filter(option_id=optionobject.pk, businessID=baker.businessID)
            detailobject.delete()

        if CakeOption.objects.filter(businessID=baker.businessID,optionID = optionobject.pk):
            cakeoption = CakeOption.objects.filter(businessID=baker.businessID,optionID = optionobject.pk)
            cakeoption.delete()

        optionobject.delete()

        return redirect('/baker/manageCake/options', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')



def storeReview(request):
    res_data = {}
    user_id = request.session.get('user')

    if user_id:
        baker = Baker.objects.get(pk=user_id)
        res_data['bakername'] = baker.name
        if request.method == "GET":
            review_list = Review.objects.filter(storeInfo=baker.businessID).order_by('cakeName')
            res_data['review_list'] = review_list
            return render(request, 'baker/storeReview.html', res_data)

    else:
        if request.method == "GET":
            res_data['comment'] = "잘못된 접근입니다. 로그인을 해주세요!"
            return render(request, 'baker/inappropriateApproach.html', res_data)
        elif request.method == "POST":
            return redirect('/')
