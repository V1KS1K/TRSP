# import datetime as dt , sys, os
# from math import sqrt as s
# print(dt.datetime.now().day) #дата 
# print(sys.path) #puti k proektu
# print(os.name)
# print(s(25))

# class cat:
#     name = None
#     age  = None

#     def __init__(self, name, age): #konstruktor
#         self.set_data(name, age)
#         self.Vvivod()


#     def set_data(self, name, age = None):
#         self.name = name
#         self.age = age
      
#     def Vvivod(self):
#         print( self.name, self.age)
    

# Cat1 = cat("lol", 15)
# Cat1.set_data("JOTH")
# Cat1.Vvivod()

# Cat2 = cat("kek", 14) 


# class Building:
#     yaer = None
#     city = None

#     def __init__(self, year, city):
#         self.yaer  = year
#         self.city = city

#     def get_info(self):
#         print(self.yaer, self.city)

# class School(Building):
#     auditor = None

#     def __init__(self, auditor, year, city):
#         super(School, self).__init__(year,city)
#         self.auditor = auditor

#     def get_info(self):
#         super().get_info()
#         print(self.auditor)

# class House(Building):
#     kvartira = None

#     def __init__(self, kvartira, year, city):
#         super(House, self).__init__(year, city)
#         self.kvartira = kvartira



# School1 = School(12 ,2020, "Moscow")
# House1 = House(18,2015, "SPB")

# School1.get_info()
