import csv
import tempfile
import os
import xlwt as xlwt
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from weasyprint import HTML

# Create your views here.
from .models import Category, Expense
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
from userpreferences.models import UserPreference
import datetime





@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=request.user)
    paginator = Paginator(expenses, 2)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    currency = UserPreference.objects.get(user=request.user).currency
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
    }
    return render(request, 'expenses/index.html', context)



@login_required(login_url='/authentication/login')
def add_expense(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values': request.POST
    }
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)
        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/add_expense.html', context)
        if not date:
            messages.error(request, 'Date is required')
            return render(request, 'expenses/add_expense.html', context)
        if not category:
            messages.error(request, 'Category is required')
            return render(request, 'expenses/add_expense.html', context)

        Expense.objects.create(owner=request.user, amount=amount, date=date, category=category, description=description)
        messages.success(request, 'Expense saved successfully')

        return redirect('expense')


@login_required(login_url='/authentication/login')
def expense_edit(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories
    }
    if request.method == 'GET':
        return render(request, 'expenses/edit_expense.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit_expense.html', context)

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/edit_expense.html', context)

        if not category:
            messages.error(request, 'Category is required')
            return render(request, 'expenses/edit_expense.html', context)

        if not date:
            messages.error(request, 'Date is required')
            return render(request, 'expenses/edit_expense.html', context)

        expense.owner = request.user
        expense.amount = amount
        expense.date = date
        expense.category = category
        expense.description = description
        expense.save()
        messages.success(request, 'Expense updated and saved  successfully')

        return redirect('expense')


def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, "Expense deleted successfully")
    return redirect('expense')

def search_expense(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user)
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date-datetime.timedelta(days=30*6)
    expense = Expense.objects.filter(owner=request.user, date__gte=six_months_ago, date__lte=todays_date)
    finalrep = {}

    def get_category(expense):
        return expense.category
    category_list = list(set(map(get_category, expense)))

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = Expense.objects.filter(owner=request.user, category=category)

        for item in filtered_by_category:
            amount += item.amount
        return amount

    for x in expense:
        for y in category_list:
            finalrep[y] = get_expense_category_amount(y)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)


def statsView(request):
    return render(request, 'expenses/stats.html')


def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=Expenses ' + str(datetime.datetime.now())+'.csv'
    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])
    expenses = Expense.objects.filter(owner=request.user)

    for expense in expenses:
        writer.writerow([expense.amount, expense.description, expense.category, expense.date])
    return response

def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Expenses ' + str(datetime.datetime.now()) + '.xls'
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Expenses')
    row = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True  ###for making the headings bold
    columns = ['Amount', 'Description', 'Category', 'Date']

    for col in range(len(columns)):
        ws.write(row, col, columns[col], font_style)

    font_style = xlwt.XFStyle()
    rows = Expense.objects.filter(owner=request.user).values_list('amount','description','category','date')
    for row_num in rows:
        row += 1
        for col in range(len(row_num)):
            ws.write(row, col, str(row_num[col]), font_style)
    wb.save(response)
    return response

def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=Expenses ' + str(datetime.datetime.now()) + '.pdf'
    response['Content-Tranfer-Encoding'] = 'binary'
    expenses = Expense.objects.filter(owner=request.user)
    sum = expenses.aggregate(Sum('amount'))
    html_string = render_to_string('expenses/pdf_output.html',{'expenses':expenses,'total':sum['amount__sum']})
    html = HTML(string=html_string)
    result = html.write_pdf()

    #for saving the result into the memory we are using tempfile
    with tempfile.NamedTemporaryFile(delete=True,) as output:
        output.write(result)
        output.flush()
        output.seek(0)
        response.write(output.read())
    return response