class OrderStatus:
    NEW = 0
    SUBMITTED = 1
    ACCEPTED = 2
    ASSIGNED = 3
    PICKED_UP = 4
    DELIVERED = 5
    COMPLETED = 6
    CANCELED = 7
    PROCESSED = 8
    CHOICES = (
        (NEW, 'New'),
        (PROCESSED, 'Processed'),
        (SUBMITTED, 'Submitted'),
        (ACCEPTED, 'Accepted'),
        (ASSIGNED, 'Assigned'),
        (PICKED_UP, 'Picked Up'),
        (DELIVERED, 'Delivered'),
        (COMPLETED, 'Completed'),
        (CANCELED, 'Canceled'),
    )


class PaymentMethod:
    CASH = 0
    MPESA = 1
    CHOICES = (
        (CASH, 'Cash'),
        (MPESA, 'MPesa')
    )


class OrderAssignmentStatus:
    ASSIGNED = 1
    ACCEPTED = 2
    REJECTED = 3
    CHOICES = (
        (ASSIGNED, 'Assigned'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected')
    )


class PaymentStatus:
    NEW = 0
    SUCCESS = 1
    WRONG_PIN = 2
    CANCEL = 3
    WRONG_NUMBER = 4
    EXPIRED = 5
    WRONG_DATA = 6
    FAILED = 7

    CHOICES = (
        (NEW, 'New'),
        (SUCCESS, 'Success'),
        (WRONG_PIN, 'Wrong PIN'),
        (CANCEL, 'Canceled'),
        (WRONG_NUMBER, 'Wrong number'),
        (WRONG_DATA, 'Wrong data'),
        (EXPIRED, 'Expired'),
        (FAILED, 'Failed'),
    )


class PushStatuses:
    ORDER_ASSIGNED = 0
    ORDER_CHANGED = 1
    ORDER_CANCELED = 2
    ORDER_REMOVED = 3
    ORDER_REASSIGNED = 4
    ORDER_PAY_SUCCEED = 5
    ORDER_PAY_FAILED = 6
