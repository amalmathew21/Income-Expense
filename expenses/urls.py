from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('',views.index,name='expense'),
    path('add-expense',views.add_expense,name='add-expense'),
    path('edit-expense/<int:id>',views.expense_edit,name='edit-expense'),
    path('delete-expense/<int:id>',views.delete_expense,name='delete-expense'),
    path('search-expense',csrf_exempt(views.search_expense),name='search-expense'),
    path('expense_summary_category',views.expense_category_summary,name='expense_summary_category'),
    path('stats',views.statsView,name='stats'),
    path('export-expense-csv',views.export_csv,name='export-expense-csv'),
    path('export-expense-excel',views.export_excel,name='export-expense-excel'),
    path('export-expense-pdf',views.export_pdf,name='export-expense-pdf'),
]
