/**
 * Client to interact with ofinta API
 * Requires jQuery
 */
class OfintaApiClient {

  constructor(apiKey) {
    this.apiKey = apiKey;
  }

  createOrder(orderData, successCallback, errorCallback) {
    var endpointUrl = '/api/v1/orders/';

    $.ajax({
      type: 'POST',
      url: endpointUrl,
      data: orderData,
      contentType: 'application/json',
      success: function (responseJson) {
        successCallback(responseJson);
      },
      fail: function () {
        errorCallback();
      },
      headers: {
        Authorization: 'ShopToken ' + this.apiKey
      },
      dataType: 'json'
    });
  }
}
