# -*- coding:utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.http import HttpResponse


admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^banners/', include('feincms_banners.urls')),

    url(
        r'^test-banner-1/$',
        lambda request: HttpResponse('Hello test banner 1'),
    ),

    url(r'', include('feincms.urls')),
)
