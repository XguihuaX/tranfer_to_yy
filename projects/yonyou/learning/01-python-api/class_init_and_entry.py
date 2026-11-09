class Customer:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id


if __name__ == "__main__":
    customer = Customer("C001")
    print(customer.customer_id)
