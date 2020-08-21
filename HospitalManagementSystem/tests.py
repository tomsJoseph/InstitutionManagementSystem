from django.test import TestCase
from django.urls import reverse
from django.test import Client
from .views import *
from .urls import *

class AllTests(TestCase):
    def test(self):
        c = Client()
        response = c.post('/accounts/login/', {'username': 'John', 'password': 'qwerty54321'})
        import pdb; pdb.set_trace()
        for url in urlpatterns:
            try:
                if '<int:pk>' in str(url.pattern):
                    response = self.client.get(reverse(url.name, kwargs={'pk' : 1}))
                    print(response.content, url.name, '<== With Parameter')
                elif '<int:patient>' in str(url.pattern):
                    response = self.client.get(reverse(url.name, kwargs={'patient' : 1}))
                    print(response.content, url.name,'<== With Parameter')
                elif '<int:p_id>' in str(url.pattern):
                    response = self.client.get(reverse(url.name, kwargs={'p_id' : 1}))
                    print(response.content, url.name, '<== With Parameter')
                elif '<int:health_id>' in str(url.pattern):
                    response = self.client.get(reverse(url.name, kwargs={'health_id' : 1}))
                    print(response.content, url.name, '<== with Parameter')
                elif '<int:hr>' in str(url.pattern):
                    response = self.client.get(reverse(url.name, kwargs={'hr' : 1}))
                    print(response.content, url.name, '<== With Parameter')
                else:
                    response = self.client.get(reverse(url.name))
                    print(response.content, url.name,'<== Withoot Parameter')
                print()
                print()
                print('---------------------------------------------------------------------------------------------------------------')
            except:
                pass
