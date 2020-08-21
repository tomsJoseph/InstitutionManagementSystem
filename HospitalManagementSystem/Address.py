from django.db import models

class Country(models.Model):

    def __str__(self):
        return self.cName

    cName = models.CharField(max_length=20)


class State(models.Model):

    def __str__(self):
        return self.sName + '-' + str(self.country)

    sName = models.CharField(max_length=20)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class District(models.Model):

    def __str__(self):
        return self.dName+' - '+self.state.sName+' - ' + self.state.country.cName

    dName = models.CharField(max_length=20)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class Address(models.Model):

    def __str__(self):
        return self.place + ', ' + str(self.district) + ', Zip: ' + str(self.zip_code)

    def get_info(self):
        if not self.private:
            return self
    pin_point = models.CharField('House Name (Land Mark if not home address).', max_length=15, null = True, default = '')
    place = models.CharField(max_length=15)
    zip_code = models.IntegerField()
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    private = models.BooleanField(default = False)
