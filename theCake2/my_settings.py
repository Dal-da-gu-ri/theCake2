DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'thecakedb',
        'USER': 'root',
        'PASSWORD': 'daldaguri',
        'HOST': 'thecake3.c6vvk46sjvco.ap-northeast-2.rds.amazonaws.com',
        'PORT': '3306',
    }
}

SECRET_KEY = 'mesn+zp#bh1k#k16(cwwd=iu!$*4u%95kcpl3g263(1r95%-go'

EMAIL = {
    'EMAIL_BACKEND':'django.core.mail.backends.smtp.EmailBackend',
    'EMAIL_USE_TLS':True,
    'EMAIL_PORT':587,
    'EMAIL_HOST':'smtp.gmail.com',
    'EMAIL_HOST_USER':'the123cake@gmail.com',
    'EMAIL_HOST_PASSWORD':'Carrie#901',
    'SERVER_EMAIL':'the123cake',
    #'DEFAULT_FROM_EMAIL':'the123cake@gmail.com'
    #'REDIRECT_PAGE':

}
