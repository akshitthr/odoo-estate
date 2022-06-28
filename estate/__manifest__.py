# -*- coding: utf-8 -*-
{
    'name': "Real Estate",

    'summary': """
        Module used to manage Real Estate Business""",

    'author': "Akshitth V. Ravichandran",
    
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        
        'views/estate_view.xml',
        'views/estate_menus.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'installable': True,
    'auto-install': False,
    'sequence': -100
}
