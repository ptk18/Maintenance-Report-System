from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Report(models.Model):

    STATUS_CHOICES = [
        ('0', 'Pending'),
        ('1', 'Approved'),
        ('2', 'Validated'),
        ('3', 'Sent'),
        ('4', 'Solved'),
        ('5', 'Finished'),
        ('6', 'Rejected'),
    ]
    reportID = models.AutoField(primary_key=True)
    reporterName = models.CharField(max_length=255)
    reporterNameReal = models.CharField(max_length=255)
    datetime = models.CharField(max_length=255,null=True)
    operationLineNumber = models.CharField(max_length=255)
    machineNumber = models.CharField(max_length=255, blank=True, null=True)
    problemDescription = models.TextField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    confirmedBy = models.CharField(max_length=255, blank=True, null=True)
    sentBy = models.CharField(max_length=255, blank=True, null=True)
    sentTo = models.CharField(max_length=255, blank=True, null=True)
    solvedBy = models.CharField(max_length=255, blank=True, null=True)
    rejectedBy = models.CharField(max_length=255, blank=True, null=True)
    problemCategory = models.CharField(max_length=255, null=True)
    subCategory = models.CharField(max_length=255, null=True)
    subCategoryForUser = models.CharField(max_length=255, null=True)
    rank = models.CharField(max_length=255, null=True)
    emailNotifyDate = models.CharField(max_length=255, blank=True, null=True)
    dueDate = models.CharField(max_length=255, blank=True, null=True)
    finishDate = models.CharField(max_length=255, blank=True, null=True)

    def get_subcategories(self):
        profession = Profession.objects.filter(profession_name=self.problemCategory).distinct()
        subcategories = SubCategory.objects.filter(profession__in=profession).distinct()
        return subcategories
   
    class Meta:
        db_table = "report"   

# Addition in the admin panel

class OperationLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_no = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.line_no
    
class SubCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subCategory = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.subCategory

class SubCategoryForUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subCategoryForUser = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.subCategoryForUser

class Profession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profession_name = models.CharField(max_length=50, unique=True)
    subCategory = models.ManyToManyField(SubCategory, blank=True)
    subCategoryForUser = models.ManyToManyField(SubCategoryForUser, blank=True)
    no_need_approval = models.BooleanField(default=False)
    no_need_approval_chief = models.BooleanField(default=False)
    
    def __str__(self):
        return self.profession_name



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    operation_line_no = models.ManyToManyField(OperationLine, blank=True)
    profession = models.ManyToManyField(Profession, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


# Solution for report 

class Solution(models.Model):
    solutionID = models.AutoField(primary_key=True)
    report = models.OneToOneField(Report, on_delete=models.CASCADE)
    solverName = models.CharField(max_length=255,null=True)
    description = models.TextField(null=True)
    datetime = models.CharField(max_length=255,null=True)
    
    class Meta:
        db_table = "solution"

# Image 
class Image(models.Model):
    report = models.ForeignKey(Report, related_name='images', on_delete=models.CASCADE, blank=True, null=True)
    imageData = models.ImageField(upload_to='reportImages/', height_field=None, width_field=None, max_length=100, blank=True, null=True)

    class Meta:
        db_table = "image"


class ImageSolution(models.Model):
    solution = models.ForeignKey(Solution, related_name='images', on_delete=models.CASCADE, blank=True, null=True)
    imageData = models.ImageField(upload_to='solutionImages/', height_field=None, width_field=None, max_length=100, blank=True, null=True)

    class Meta:
        db_table = "image_solution"
