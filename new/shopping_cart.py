"""
An example for a shopping cart. More of a sketch really, of what it could look
like. Some details (like names of mutator function) have not settled yet. But
something like this should certainly be possible.
"""

from flexx import app, ui


class Store(app.PyModel):
    """ A server-side model that tracks the inventory at the server. Shared by all
    clients.
    """
    class State:
        
        products = app.dict_prop(doc='Products in store')
    
    def init(self):
        
        self.receive_products([dict(id=1, name='rubber duck', quantity=12),
                               dict(id=2, name='cake', quantity=16),
                               dict(id=3, name='IPhone', quantity=3),
                               ])

    @app.action
    def receive_products(self, *products):
        product_dict = {}
        for product in products:
            product_dict[product.id] = product
        self._set_prop('products', product_dict)
    
    @app.action
    def take_product(product):
        if product.id in self.products:
            p = self.products[product.id].copy()
            p.quantity -= 1
            self._update_prop('products', product.id, p)


# global store, shared by all clients
store = Store()


class Cart(app.Model):
    """ Representation of (the bisiness logic of) a shopping cart.
    """
    
    class State:
        
        added = app.dict_prop(doc='Products in the cart')
        checkout_status = app.prop(0, settable=int, doc='Status of checkout')
    
    class JS:
        
        @app.action
        def add_product(self, product):
            # Add to cart (or increase counter of product in cart)
            if product.id in self.added:
                p = self.added[product.id].copy()
                p.quantity += 1
                self._update_prop('added', p.id, p)
            else:
                p = dict(id=product.id, name=product.name, quantity=1)
                self._push_prop('added', p.id, p)
            # Remove from store by invoking an action at the store
            self.root.store.take_product(product)
        
        @app.action
        def checkout(self, products):
            saved_cart_items = self.added.copy()
            self._set_prop('added', {})
            self._set_prop('checkout_status', 0)
            self.buy_products(products,
                              self.checkout_success,
                              lambda: self.checkout_fail(saved_cart_items))
        
        @app.action
        def checkout_success(self):
            self._set_prop('checkout_status', 1)
        
        @app.action
        def checkout_fail(self, saved_cart_items):
            self._set_prop('added', saved_cart_items)
            self._set_prop('checkout_status', -1)


class StoreWidget(ui.Widget):
    """ The main widget.
    """
    
    def init(self):
        
        # Models that represent business logic
        self.store = store
        self.cart = Cart()
    
    class JS:
        
        def init(self):
            
            # Views
            self.catalog = ui.SomeWidgetThatDisplaysProducts()
            self.cartwidget = ui.SomeWidgetThatDisplaysTheCart()
        
        @reaction('store.products')
        def _update_quantities(self, *events):
            for ev in events:
                prod_id = ev.key
                quantity = ev.data.quantity
                self.catalog.set_quantity(prod_id, quantity)


if __name__ == '__main__':
    app.serve(StoreWidget)
    app.run()
