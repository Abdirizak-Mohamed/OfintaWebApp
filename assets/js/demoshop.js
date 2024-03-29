$(document).ready(function () {
  var paymentTimer;
  var webhookUrl = '/mpesa-result/';

  var $demoUserForm = $('#demoshop-user-form');

  var orderNumber = Math.round(Math.random() * (9999999999 - 0) + 0).toString();
  $('#order-number').text(orderNumber);

  function setStatus(message) {
    $('#status').text(message).show();
  }

  function clearStatus() {
    $('#status').text('').hide();
  }


  function formDataToObject(formData) {
    var formDataJson = {};
    for (var i in formData) {
      const fieldName = formData[i].name,
        fieldValue = formData[i].value;
      formDataJson[fieldName] = fieldValue;
    }
    return formDataJson;
  }

  function formIsFilled($form) {
    var formFilled = true;
    $form.find('input').each(function() {
      if ($(this).val() === '') {
        formFilled = false;
      }
    });
    return formFilled;
  }

  function prepareRequestData($form) {
    var userData = $form.serializeArray();
    var requestData = formDataToObject(userData);
    requestData['order_number'] = orderNumber;
    requestData['shipping_address'] = {'address': requestData['address']};
    requestData['positions'] = [];
    var $demoProductsForms = $('.demoshop-product-form');
    $demoProductsForms.each(function(i, productForm) {
      if (formIsFilled($(productForm))) {
        var productFormDataJson = formDataToObject($(productForm).serializeArray());
        requestData['positions'].push(productFormDataJson);
      }
    });
    return requestData;
  }

  function getTransaction(orderId) {
    var url = 'transaction/' + orderId + '/status/';
    $.get(url, function(data) {
      var txnStatus = data.status;

      if (txnStatus !== 'New') {
        if (txnStatus === 'Success') {
          alert('Verification code sent by sms and on your email');
        } else {
          alert('Failed to process transaction. Transaction status: ' + txnStatus);
        }
        clearInterval(paymentTimer);
      }
    });
  }

  function processResponseType(responseType, orderId) {
    var ResultCode, ResultDesc,
      requestFromMpesa = {
        'Body': {
          'stkCallback': {
            'MerchantRequestID': 'mr_id',
            'CheckoutRequestID': 'cr_id'
          }
        }
      };

    if (responseType === 'success') {
      ResultCode = 0;
      ResultDesc = 'The service request is processed successfully.';
    } else if (responseType === 'wrong_pin') {
      ResultCode = 10;
      ResultDesc = 'The initiator information is invalid.';
    } else if (responseType === 'canceled') {
      ResultCode = 11;
      ResultDesc = 'Request cancelled by user';
    } else if (responseType === 'wrong_data') {
      ResultCode = 12;
      ResultDesc = 'Some error message';
    } else if (responseType === 'wo_imititation') {
      setStatus('Waiting for response from mpesa');
      paymentTimer = setInterval(function() {getTransaction(orderId)}, 5000);
    }
    requestFromMpesa['Body']['stkCallback']['ResultCode'] = ResultCode;
    requestFromMpesa['Body']['stkCallback']['ResultDesc'] = ResultDesc;
    requestFromMpesa = JSON.stringify(requestFromMpesa);

    if (responseType !== 'wo_imititation') {
      $.post(webhookUrl, requestFromMpesa, function(data) {
        if (responseType === 'success') {
          alert('Verification code is ' + data['verification_code']);
        } else if (ResultDesc) {
          setStatus(ResultDesc);
        }
      });
    }
  }

  $demoUserForm.on('submit', function () {
    clearStatus();
    clearInterval(paymentTimer);
    var responseType = $('#response-type').val();
    var requestData = prepareRequestData($(this));
    var paymentMethod = requestData.payment_method;

    apiClient.createOrder(
      JSON.stringify(requestData),
      function (responseJson) {
        var orderId = responseJson['id'];
        console.log('Order successfully created');
        if (paymentMethod == 1) {
          processResponseType(responseType, orderId);
        } else {
          alert('New order with cash payment created')
        }
      },
      function () {
        setStatus('Failed to create new order');
      }
    );
    orderNumber = Math.round(Math.random() * (9999999999 - 0) + 0).toString();
    $('#order-number').text(orderNumber);
    return false;
  });

  $('#new-product-link').on('click', function() {
    var $extraForm = $('.demoshop-product-form.extra-form');
    var $extraFormCopy = $extraForm.clone();
    $('.products').append($extraFormCopy);
    $extraFormCopy.show().removeClass('extra-form');
    return false;
  });
});
