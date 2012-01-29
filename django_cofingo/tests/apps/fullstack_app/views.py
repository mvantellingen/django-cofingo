from django.template.response import TemplateResponse


def index(request):
    return TemplateResponse(request, 'fullstack_app/index.html')
