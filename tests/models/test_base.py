def test_special_camel():
    from ftl.models.base import special_camel

    assert special_camel("type_") == "type"
    assert special_camel("id_") == "id"
    assert special_camel("class_") == "class"
