# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils.nestedset import get_descendants_of

def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		{
			"label": _("Item Code"),
			"fieldtype": "Link",
			"fieldname": "item_code",
			"options": "Item",
			"width": 120
		},
		{
			"label": _("Item Name"),
			"fieldtype": "Data",
			"fieldname": "item_name",
			"width": 140
		},
		{
			"label": _("Item Group"),
			"fieldtype": "Link",
			"fieldname": "item_group",
			"options": "Item Group",
			"width": 120
		},
		{
			"label": _("Description"),
			"fieldtype": "Data",
			"fieldname": "description",
			"width": 150
		},
		{
			"label": _("Quantity"),
			"fieldtype": "Float",
			"fieldname": "quantity",
			"width": 150
		},
		{
			"label": _("UOM"),
			"fieldtype": "Link",
			"fieldname": "uom",
			"options": "UOM",
			"width": 100
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			"options": "Currency",
			"width": 120
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"options": "Currency",
			"width": 120
		},
		{
			"label": _("Sales Order"),
			"fieldtype": "Link",
			"fieldname": "sales_order",
			"options": "Sales Order",
			"width": 100
		},
		{
			"label": _("Transaction Date"),
			"fieldtype": "Date",
			"fieldname": "transaction_date",
			"width": 90
		},
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 100
		},
		{
			"label": _("Customer Name"),
			"fieldtype": "Data",
			"fieldname": "customer_name",
			"width": 140
		},
		{
			"label": _("Customer Group"),
			"fieldtype": "Link",
			"fieldname": "customer_group",
			"options": "customer Group",
			"width": 120
		},
		{
			"label": _("Territory"),
			"fieldtype": "Link",
			"fieldname": "territory",
			"options": "Territory",
			"width": 100
		},
		{
			"label": _("Project"),
			"fieldtype": "Link",
			"fieldname": "project",
			"options": "Project",
			"width": 100
		},
		{
			"label": _("Delivered Quantity"),
			"fieldtype": "Float",
			"fieldname": "delivered_quantity",
			"width": 150
		},
		{
			"label": _("Billed Amount"),
			"fieldname": "rate",
			"options": "billed_amount",
			"width": 120
		},
		{
			"label": _("Company"),
			"fieldtype": "Link",
			"fieldname": "company",
			"options": "Company",
			"width": 100
		}
	]

def get_data(filters):

	data = []

	company_list = get_descendants_of("Company", filters.get("company"))
	company_list.append(filters.get("company"))

	customer_details = get_customer_details()
	sales_order_records = get_sales_order_details(company_list, filters)

	for record in sales_order_records:
		customer_record = customer_details.get(record.customer)
		row = {
			"item_code": record.item_code,
			"item_name": record.item_name,
			"item_group": record.item_group,
			"description": record.description,
			"quantity": record.qty,
			"uom": record.uom,
			"rate": record.base_rate,
			"amount": record.base_amount,
			"sales_order": record.name,
			"transaction_date": record.transaction_date,
			"customer": record.customer,
			"customer_name": customer_record.customer_name,
			"customer_group": customer_record.customer_group,
			"territory": record.territory,
			"project": record.project,
			"delivered_quantity": flt(record.delivered_qty),
			"billed_amount": flt(record.billed_amt),
			"company": record.company
		}
		data.append(row)

	return data

def get_conditions(filters):
	conditions = ''
	if filters.get('item_group'):
		conditions += "AND so_item.item_group = %s" %frappe.db.escape(filters.item_group)

	if filters.get('from_date'):
		conditions += "AND so.transaction_date >= '%s'" %filters.from_date

	if filters.get('to_date'):
		conditions += "AND so.transaction_date <= '%s'" %filters.to_date

	return conditions

def get_customer_details():
	details = frappe.get_all('Customer',
		fields=['name', 'customer_name', "customer_group"])
	customer_details = {}
	for d in details:
		customer_details.setdefault(d.name, frappe._dict({
			"customer_name": d.customer_name,
			"customer_group": d.customer_group
		}))
	return customer_details

def get_sales_order_details(company_list, filters):
	conditions = get_conditions(filters)

	return frappe.db.sql("""
		SELECT
			so_item.item_code, so_item.item_name, so_item.item_group,
			so_item.description, so_item.qty, so_item.uom,
			so_item.base_rate, so_item.base_amount, so.name,
			so.transaction_date, so.customer, so.territory,
			so.project, so_item.delivered_qty,
			so_item.billed_amt, so.company
		FROM
			`tabSales Order` so, `tabSales Order Item` so_item
		WHERE
			so.name = so_item.parent
			AND so.company in ({0})
			AND so.docstatus = 1 {1}
	""".format(','.join(["%s"] * len(company_list)), conditions), tuple(company_list), as_dict=1)
