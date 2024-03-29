$(document).ready(function () {
  function getPayment(orderId) {
    var url = 'transaction/' + orderId + '/status/';
    $.get(url, function(data) {
      var paymentStatus = data.status;

      if (paymentStatus !== 'New') {
        if (paymentStatus === 'Success') {
          window.location.href = '/orders/' + paymentLinkId + '/paid'
        } else {
          if (paymentStatus === 'Canceled') {
            window.location.href = '/orders/' + paymentLinkId + '/';
          } else {
            localStorage.setItem('payment_error_' + paymentLinkId, paymentStatus);
            window.location.href = '/orders/' + paymentLinkId + '/';
          }
        }
        clearInterval(paymentTimer);
      }
    });
  }

  if (payMpesa) {
    paymentTimer = setInterval(function() {getPayment(orderId)}, 5000);
  }
});
