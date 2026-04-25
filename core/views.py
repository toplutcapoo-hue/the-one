from django.shortcuts import render, redirect
from .models import Expense
from .forms import ExpenseForm

def index(request):
    expenses = Expense.objects.all().order_by('-date')
    total = sum(exp.amount for exp in expenses)

    return render(request, 'index.html', {
        'expenses': expenses,
        'total': total
    })


def add_expense(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ExpenseForm()

    return render(request, 'add.html', {'form': form})
