
from flexx import app


class Store(app.Model):
    
    class State:
        
        cart = app.dict_prop(doc='Products in the cart')
        products = app.dict_prop(doc='Products in store')
        checkout_status = app.prop(0, settable=int, doc='Status of checkout')
        # todo: could put products in a shared PyModel
    
    class JS:
        
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
        def add_to_cart(self, product):
            # Add to cart (or increase counter of product in cart)
            if product.id in self.cart and self.cart[product.id].quantity > 0:
                p = self.cart[product.id].copy()
                p.quantity += 1
                self._update_prop('cart', p.id, p)
            else:
                p = dict(id=product.id, name=product.name, quantity=1)
                self._push_prop('cart', p.id, p)
            # Remove from store
            # todo: we could also do this is a reaction in case cart and products are not on the same model
            p = self.products[product.id].copy()
            p.quantity -= 1
            self._update_prop('products', p.id, p)
        
        @app.action
        def checkout(self, products):
            saved_cart_items = self.cart.copy()
            self._set_prop('cart', {})
            self._set_prop('checkout_status', 0)
            self.buy_products(products,
                              self.checkout_success,
                              lambda: self.checkout_fail(saved_cart_items))
        
        @app.action
        def checkout_success(self):
            self._set_prop('checkout_status', 1)
        
        @app.action
        def checkout_fail(self, saved_cart_items):
            self._set_prop('cart', saved_cart_items)
            self._set_prop('checkout_status', -1)
