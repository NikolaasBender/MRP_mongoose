import shopify

def add_order(order: shopify.resources.order.Order):
    for item in order.line_items:
        if hasattr(item, 'properties') and item.properties:
            print("      Properties:")
            prop  = item.properties[0]
            if prop.name == "Color Set" and prop.value == "Custom":
                # get item type
        