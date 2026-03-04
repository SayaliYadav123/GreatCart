from django.db import models
from django.urls import reverse

# Create your models here.
class Gender(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'gender'
        verbose_name_plural = 'genders'

    def __str__(self):
        return self.name



class Category(models.Model):
    gender = models.ForeignKey(
        Gender,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    category_name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        unique_together = ('gender', 'slug')

    def get_url(self):
        return reverse(
            'products_by_category',
            args=[self.gender.slug, self.slug]
        )

    def __str__(self):
        gender_name = self.gender.name if self.gender else "No Gender"
        return f"{gender_name} - {self.category_name}"


from django.db import models

# Create your models here.
