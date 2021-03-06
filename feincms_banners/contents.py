from __future__ import absolute_import, unicode_literals

from django.db import models
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from feincms_banners.models import Banner

from feincms.admin.item_editor import FeinCMSInline
from django.contrib.sites.models import get_current_site

class BannerContentInline(FeinCMSInline):
    raw_id_fields = ('specific',)


class BannerContent(models.Model):
    feincms_item_editor_inline = BannerContentInline

    is_section_aware = True

    specific = models.ForeignKey(
        Banner, verbose_name=_('specific'),
        blank=True, null=True, limit_choices_to={'is_active': True},
        help_text=_(
            'If you leave this empty, a random banner will be selected.'))
    type = models.CharField(
        _('type'), max_length=20, choices=Banner.TYPE_CHOICES)

    class Meta:
        abstract = True
        verbose_name = _('banner')
        verbose_name_plural = _('banners')

    def render(self, **kwargs):

        request = kwargs['request']
        current_site = get_current_site(request)

        if self.specific:
            allowed_sites =  self.specific.sites.all()
            if len(allowed_sites) > 0 and  current_site not in allowed_sites:
                return ''

            specific_is_active = (
                self.specific.is_active
                and self.specific.active_from <= timezone.now()
                and (
                    not self.specific.active_until
                    or self.specific.active_until >= timezone.now()
                ))

            if specific_is_active:
                banner = self.specific
                type = banner.type
            else:
                return ''
        else:
            valid_banner = None
            possible_banners = Banner.objects.active().filter(
                type=self.type,
                ).select_related('mediafile').order_by('?')
            for banner in possible_banners:
                if banner.allowed_for_site(current_site):
                    valid_banner = banner
                    break

            if not valid_banner:
                return ''
            type = self.type

        Banner.objects.filter(id=banner.id).update(embeds=F('embeds') + 1)

        return render_to_string(
            [
                'content/banner/%s.html' % type,
                'content/banner/default.html',
            ],
            {'content': self, 'banner': banner},
            context_instance=kwargs.get('context'))

