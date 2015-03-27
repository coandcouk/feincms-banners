from __future__ import absolute_import, unicode_literals

from random import choice

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site


from feincms.module.medialibrary.fields import MediaFileForeignKey
from feincms.module.medialibrary.models import MediaFile
import re


def generate_key():
    return ''.join([
        choice('abcdefghijklmnopqrstuvwxyz0123456789-_') for i in range(40)])


class BannerManager(models.Manager):
    def active(self):
        return self.filter(
            Q(is_active=True, active_from__lte=timezone.now())
            & (
                Q(active_until__isnull=True)
                | Q(
                    active_until__isnull=False,
                    active_until__gte=timezone.now()
                )
            )
        )


class Banner(models.Model):
    SKYSCRAPER = 'skyscraper'
    LEADERBOARD = 'leaderboard'
    BOX = 'box'

    TYPE_CHOICES = (
        (SKYSCRAPER, _('skyscraper')),
        (LEADERBOARD, _('leaderboard')),
        (BOX, _('box')),
    )


    TARGET_SELF = '_self'
    TARGET_BLANK = '_blank'

    TARGET_CHOICES = (
        (TARGET_SELF, _('self')),
        (TARGET_BLANK, _('blank'))
    )

    is_active = models.BooleanField(_('is active'), default=True)
    name = models.CharField(
        _('name'), max_length=100, help_text=_(
            'Only for internal use, will not be shown on the website.'))
    mediafile = MediaFileForeignKey(MediaFile, verbose_name=_('media file'))
    url = models.URLField(_('URL'))
    type = models.CharField(_('type'), max_length=20, choices=TYPE_CHOICES)
    code = models.CharField(
        _('code'), max_length=40, default=generate_key, unique=True)

    active_from = models.DateTimeField(
        _('active from'), default=timezone.now)
    active_until = models.DateTimeField(
        _('active until'), blank=True, null=True)

    embeds = models.PositiveIntegerField(
        _('embeds'), default=0, editable=False,
        help_text=_(
            'How many times has this banner been embdedded on a website?'))
    impressions = models.PositiveIntegerField(
        _('impressions'), default=0,
        editable=False,
        help_text=_(
            'How many times has an impression been registered using'
            ' a Javascript callback, verifying that it actually was a'
            ' browser? (Too low because of network issues and deactivated'
            ' Javascript support in some browsers.)'))

    sites = models.ManyToManyField(Site, verbose_name=_('Site'), blank=True, null=True)
    target = models.CharField(_('target'), max_length=20, choices=TARGET_CHOICES, default=TARGET_SELF)

    objects = BannerManager()

    class Meta:
        ordering = ['-active_from']
        verbose_name = _('banner')
        verbose_name_plural = _('banners')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('banner_click', (), {'code': self.code})

    @models.permalink
    def impression_url(self):
        return ('banner_impression', (), {'code': self.code})

    def click(self, request):
        from ua_parser import user_agent_parser
        user_agent_string = request.META.get('HTTP_USER_AGENT')
        result_dict = user_agent_parser.Parse(user_agent_string)
        print 'device family' + str(result_dict['device'])

        if result_dict['device']['family'] != 'Spider':
            self.clicks.create(
				ip=request.META.get('REMOTE_ADDR'),
				user_agent=request.META.get('HTTP_USER_AGENT', ''),
				referrer=request.META.get('HTTP_REFERER', ''),
			)

    def click_count(self):
        return self.clicks.count()
    click_count.short_description = _('click count')


class Click(models.Model):
    banner = models.ForeignKey(
        Banner, verbose_name=_('banner'), related_name='clicks')
    timestamp = models.DateTimeField(_('timestamp'), default=timezone.now)
    ip = models.IPAddressField(_('IP'), blank=True, null=True)
    user_agent = models.TextField(_('user agent'), blank=True, default='')
    referrer = models.TextField(_('referrer'), blank=True, default='')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('click')
        verbose_name_plural = _('clicks')
