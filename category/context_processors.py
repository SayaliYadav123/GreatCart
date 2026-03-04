# from .models import Category

# def menu_links(request):
#     links = Category.objects.all()
#     return dict(links=links)
# from .models import Category

# def gender_categories(request):
#     return {
#         'men_categories': Category.objects.filter(gender__slug='men'),
#         'women_categories': Category.objects.filter(gender__slug='women'),
#         'kids_categories': Category.objects.filter(gender__slug='kids'),
#     }

from category.models import Category
from category.models import Gender

def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)

def gender_categories(request):
    return {
        'men_categories':         Category.objects.filter(gender__slug='men'),
        'women_categories':       Category.objects.filter(gender__slug='women'),
        'kids_categories':        Category.objects.filter(gender__slug='kids'),
        'accessories_categories': Category.objects.filter(gender__slug='accessories'),
        'all_genders':            Gender.objects.all(),
    }
