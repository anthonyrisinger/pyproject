import pytest


def test_configurable(props):
    class C:
        @props.config(one=1)
        def normal(instance, context):
            return context.config.one, context.__class__
        @props.config()
        def empty(instance, context):
            return 2, context.__class__
        @props.config
        def missing(instance, context):
            return 3, context.__class__

    assert C.normal == (1, props.config.OWNER.GET)
    assert C.empty == (2, props.config.OWNER.GET)
    assert C.missing == (3, props.config.OWNER.GET)

    c = C()
    assert c.normal == (1, props.config.INSTANCE.GET)
    assert c.empty == (2, props.config.INSTANCE.GET)
    assert c.missing == (3, props.config.INSTANCE.GET)


def test_caching(props):
    class C:
        called = 0
        @props.caching
        def normal(instance, context):
            C.called += 1
        @props.caching(cache=False)
        def disabled(instance, context):
            C.called += 1
        @props.caching
        def cache_off(instance, context):
            C.called += 1
            context.value = None
            context.cache = False
            return context
        @props.caching(cache=False)
        def cache_on(instance, context):
            C.called += 1
            context.value = None
            context.cache = True
            return context

    C.normal
    C.normal
    assert C.called == 2
    C.called = 0

    C.disabled
    C.disabled
    assert C.called == 2
    C.called = 0

    C.cache_off
    C.cache_off
    assert C.called == 2
    C.called = 0

    C.cache_on
    C.cache_on
    assert C.called == 2
    C.called = 0

    c = C()

    c.normal
    c.normal
    assert c.called == 1
    C.called = 0

    c.disabled
    c.disabled
    assert c.called == 2
    C.called = 0

    c.cache_off
    c.cache_off
    assert c.called == 2
    C.called = 0

    c.cache_on
    c.cache_on
    assert c.called == 1
    C.called = 0
