import csv
import tempfile

import xlwt
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import Source, Income
from userpreferences.models import UserPreference
from django.contrib import messages
from django.core.paginator import Paginator
import  json
from django.http import JsonResponse, HttpResponse
import datetime

# Create your views here.

@login_required(login_url='/authentication/login')
def index(request):
    categories = Source.objects.all()
    income = Income.objects.filter(owner=request.user)
    paginator = Paginator(income, 2)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator,page_number)
    currency = UserPreference.objects.get(user=request.user).currency
    context = {
        'income': income,
        'page_obj' : page_obj,
        'currency' : currency,
    }
    return render(request, 'income/index.html', context)

@login_required(login_url='/authentication/login')
def add_income(request):
    sources = Source.objects.all()
    context = {
        'sources': sources,
        'values': request.POST
    }
    if request.method == 'GET':
        return render(request, 'income/add_income.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['income_date']
        source = request.POST['source']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/add_income.html', context)
        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'income/add_income.html', context)
        if not date:
            messages.error(request, 'Date is required')
            return render(request, 'income/add_income.html', context)
        if not source:
            messages.error(request, 'Category is required')
            return render(request, 'income/add_income.html', context)

        Income.objects.create(owner=request.user, amount=amount, date=date, source=source, description=description)
        messages.success(request, 'Income saved successfully')

        return redirect('/income')


@login_required(login_url='/authentication/login')
def edit_income(request, id):
    income = Income.objects.get(pk=id)
    sources = Source.objects.all()
    context = {
        'income': income,
        'values': income,
        'sources': sources
    }
    if request.method == 'GET':
        return render(request, 'income/edit_income.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['income_date']
        source = request.POST['source']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/edit_income.html', context)

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'income/edit_income.html', context)

        if not source:
            messages.error(request, 'Source is required')
            return render(request, 'income/edit_income.html', context)

        if not date:
            messages.error(request, 'Date is required')
            return render(request, 'income/edit_income.html', context)

        income.owner = request.user
        income.amount = amount
        income.date = date
        income.source = source
        income.description = description
        income.save()
        messages.success(request, 'Income updated and saved  successfully')

        return redirect('income')

def delete_income(request,id):
    income = Income.objects.get(pk=id)
    income.delete()
    messages.success(request,"Income deleted successfully")
    return redirect('income')


def search_income(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        incomes = Income.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Income.objects.filter(
            date__istartswith=search_str, owner=request.user) | Income.objects.filter(
            description__icontains=search_str, owner=request.user) | Income.objects.filter(
            source__icontains=search_str, owner=request.user)
        data = incomes.values()
        return JsonResponse(list(data), safe=False)

def income_source_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date-datetime.timedelta(days=30*6)
    income = Income.objects.filter(owner=request.user, date__gte=six_months_ago, date__lte=todays_date)
    finalrep = {}

    def get_source(income):
        return income.source
    category_list = list(set(map(get_source, income)))

    def get_income_source_amount(source):
        amount = 0
        filtered_by_source = Income.objects.filter(owner=request.user, source=source)

        for item in filtered_by_source:
            amount += item.amount
        return amount

    for x in income:
        for y in category_list:
            finalrep[y] = get_income_source_amount(y)

    return JsonResponse({'income_source_data': finalrep}, safe=False)


def statsView(request):
    return render(request, 'income/stats.html')

def export_income_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=Income ' + str(datetime.datetime.now())+'.csv'
    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Source', 'Date'])
    incomes = Income.objects.filter(owner=request.user)

    for income in incomes:
        writer.writerow([income.amount, income.description, income.source, income.date])
    return response

def export_income_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Income ' + str(datetime.datetime.now()) + '.xls'
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Incomes')
    row = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True  ###for making the headings bold
    columns = ['Amount', 'Description', 'Source', 'Date']

    for col in range(len(columns)):
        ws.write(row, col, columns[col], font_style)

    font_style = xlwt.XFStyle()
    rows = Income.objects.filter(owner=request.user).values_list('amount','description','source','date')
    for row_num in rows:
        row += 1
        for col in range(len(row_num)):
            ws.write(row, col, str(row_num[col]), font_style)
    wb.save(response)
    return response

def export_income_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=Income ' + str(datetime.datetime.now()) + '.pdf'
    response['Content-Tranfer-Encoding'] = 'binary'
    incomes = Income.objects.filter(owner=request.user)
    sum = incomes.aggregate(Sum('amount'))
    html_string = render_to_string('income/pdf_output.html',{'incomes':incomes,'total':sum['amount__sum']})
    html = HTML(string=html_string)
    result = html.write_pdf()

    #for saving the result into the memory we are using tempfile
    with tempfile.NamedTemporaryFile(delete=True,) as output:
        output.write(result)
        output.flush()
        output.seek(0)
        response.write(output.read())
    return response





