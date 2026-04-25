from django.shortcuts import render
from .models import Expense

def home(request):
    all_expenses = Expense.objects.all()
    # Replace 'index.html' with your actual main file name
    return render(request, 'index.html', {'expenses': all_expenses})
