$(document).ready(function () {
  var $addProductButton = $('#add-product'),
      $priceListItemsSelect = $('#id_items'),
      $totalFormsInput = $('#id_positions-TOTAL_FORMS'),
      $positionRows = $('#position-rows'),
      $positionTotalPriceValue = $('.positions-total-value'),
      $saveOrderBtn = $('#save-payment-link-btn'),
      $orderForm = $('#order-form'),
      priceFieldSelector = '.price-field',
      quantityFieldSelector = '.quantity-field',
      priceInputSelector = '.price-field input',
      quantityInputSelector = '.quantity-field input',
      positionRowSelector = '.position-row',
      removePositionRowSelector = '.remove-position-item';

  // set total forms initial to 0
  $totalFormsInput.val($(positionRowSelector).length);

  /**
   * Calculate and update total price
   */
  function updateTotalPrice() {
    var totalPrice = 0,
        $positionRows = $(positionRowSelector);

    $.each($positionRows, function(i, positionRow) {
      var $positionRow = $(positionRow);

      var $priceInput = $positionRow.find(priceFieldSelector).find('input');
      var $quantityInput = $positionRow.find(quantityFieldSelector).find('input');
      totalPrice += parseFloat($priceInput.val()) * parseFloat($quantityInput.val());
    });
    $positionTotalPriceValue.text(totalPrice);
  }

  /**
   * Add position from the pricelist
   */
  function addPosition(priceListItemId) {
    var numForms = parseInt($totalFormsInput.val());
    var url = '/management/pricelist/' + priceListItemId + '/add_position/?num_forms=' + numForms;
    $.get(url, function(data) {
      var $positionRow = $(data.html);
      $positionRows.append($positionRow);

      updateTotalPrice();

      // set total forms value
      $totalFormsInput.val($(positionRowSelector).length);
    });
  }

  $addProductButton.on('click', function() {
    addPosition($priceListItemsSelect.val());
  });

  /**
   * Remove position item click
   */
  $(document).on('click', removePositionRowSelector, function() {

    // remove position row
    var $positionRow = $(this).closest(positionRowSelector);
    $positionRow.remove();

    // set total forms value
    $totalFormsInput.val($(positionRowSelector).length);

    updateTotalPrice();
    return false;
  });

  /**
   * Position price change
   */
  $(document).on('keyup', priceInputSelector, function() {
    updateTotalPrice();
  });


  /**
   * Position price change
   */
  $(document).on('change', priceInputSelector, function() {
    updateTotalPrice();
  });

  /**
   * Position quantity change
   */
  $(document).on('keyup', quantityInputSelector, function() {
    updateTotalPrice();
  });

  /**
   * Position quantity change
   */
  $(document).on('change', quantityInputSelector, function() {
    updateTotalPrice();
  });


  /**
   * Search
   */
  var $searchInput = $('#id_query'),
      $priceListItems = $('.pricelist-items'),
      addPriceListItemSelector = '.add-pricelist-item';

  /**
   * Listen to query input (search starting from 3rd letter)
   */
  $searchInput.keyup(function() {
    var query = $(this).val(),
        searchUrl = $(this).closest('#search-form').attr('action'),
        url = searchUrl;

    if (query.length > 0) {
      url += '?q=' + query;
    }

    $searchInput.prop('disabled', true);
      $.get(url, function(data) {
        $priceListItems.html(data.html);

        $searchInput.prop('disabled', false);
        $searchInput.focus();
      });
  });

  /**
   * Add item from the price list to the positions
   */
  $(document).on('click', addPriceListItemSelector, function() {
    addPosition($(this).data('id'));
  });


  /**
   * Save order form button click
   */
  $saveOrderBtn.click(function() {
    $orderForm.submit();
  });
});
