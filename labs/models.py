from django.db import models
import settings


class BlankModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        s = "[" + super().__str__() + "]:" if settings.DEBUG else ""
        if hasattr(self, 'name'):
            return s + str(self.pk) + ", " + self.name
        return s + "pk=" + str(self.pk)
