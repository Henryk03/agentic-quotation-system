

def save_product(
        name: str,
        availability: str,
        price: str,
        link: str,
    ) -> dict[str, str]:
    """
    Create a structured representation of a product.

    This function builds and returns a dictionary containing the
    main attributes of a product. It does not perform any IO
    operations or persistence; it only structures the provided
    data into a standardized format.

    Parameters
    ----------
    name : str
        The name or title of the product.

    availability : str
        The availability status of the product (e.g., "In stock",
        "Out of stock", "Pre-order").

    price : str
        The product price as a string, including currency symbol
        if applicable (e.g., "€999", "$499.00").

    link : str
        The URL linking to the product detail page.

    Returns
    -------
    dict[str, str]
        A dictionary containing the product information with the
        following structure:

        {
            "name": <str>,
            "availability": <str>,
            "price": <str>,
            "link": <str>
        }

    Notes
    -----
    All fields are returned exactly as provided. No validation,
    normalization, or formatting is applied to the input values.
    """

    product_info: dict[str, str] = {
        "name": name,
        "availability": availability,
        "price": price,
        "link": link,
    }

    return product_info