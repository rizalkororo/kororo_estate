# -*- coding: utf-8 -*-
{
    'name': "Kororo Estate",

    'summary': "Kororo Sampe Estate App",

    'description': """
        Estate Sample App
    """,

    'author': "Kororo",
    'website': "https://www.kororo.co",
    'category': 'kororo/estate',
    'version': '0.1',
    'module_type': 'official',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/user_estate_status.xml',
        'views/property_tags_view.xml',
        'views/property_type_views.xml',
        'views/property_offer.xml',
        'views/property_type_action.xml',
        'views/estate_property_views.xml',
        'views/estate_form_view.xml',
        'views/estate_search_view.xml',
        'views/property_type_form_view.xml',
        'views/estate_action_view.xml',
        'views/menu.xml',
    ],
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'estate/static/src/scss/main.scss',
        ],
    },

}
