# flake8: noqa N802
import contextlib
import types

import mock
import pytest
from environ import Env, sys, os

from boogie.configurations import Conf, DjangoConf, save_configuration
from boogie.configurations.descriptors import EnvProperty, EnvDescriptor, env, env_property


@contextlib.contextmanager
def environ(env=None):
    env = {} if env is None else env
    try:
        with mock.patch.object(Env, 'ENVIRON', env):
            with mock.patch.object(os, 'environ', env):
                yield env
    finally:
        pass


class TestConfWithEnv:
    @pytest.fixture(scope='class')
    def conf_class(self):
        class ConfClass(Conf):
            EVAR = env(42)

        return ConfClass

    @pytest.fixture
    def conf(self, conf_class):
        return conf_class()

    def test_do_not_have_get_value_method(self, conf_class):
        with pytest.raises(AttributeError):
            print(conf_class.get_value)
            print(Conf.get_value)

        with pytest.raises(AttributeError):
            print(conf_class().get_value)
            print(Conf().get_value)

        with pytest.raises(AttributeError):
            print(DjangoConf.get_value)

    def test_can_create_env_descriptors(self):
        assert isinstance(env(42), EnvDescriptor)
        assert not isinstance(env_property(type=int), EnvProperty)

    def test_class_env_descriptor_is_correctly_initialized(self, conf_class):
        descr = conf_class.EVAR
        assert descr.name == 'EVAR'
        assert descr.type == int
        assert descr.kwargs == {}
        assert descr.default == 42

    def test_can_set_name_of_environment_variable(self):
        class Foo(Conf):
            var = env(42, name='answer')

        assert Foo.var.name == 'answer'

        with environ({'var': 0}):
            assert Foo().var == 42

        with environ({'answer': 0}):
            assert Foo().var == 0

    def test_check_type_validity(self):
        with pytest.raises(ValueError):
            env(42, type='bad')

    def test_conf_can_access_default_value(self, conf):
        with environ():
            assert conf.EVAR == 42

    def test_conf_can_access_environ_value(self, conf):
        with environ({'EVAR': '10'}):
            assert conf.EVAR == 10

    def test_value_is_cached(self, conf):
        with environ():
            assert conf.EVAR == 42
        with environ({'EVAR': '10'}):
            assert conf.EVAR == 42


class TestConfWithEnvProperty:
    @pytest.fixture(scope='class')
    def conf_class(self):
        class ConfClass(Conf):
            EVAR = env(42)

            @env_property(default=0)
            def EPROP(self, value):
                return value + 1

        return ConfClass

    def test_can_create_env_property(self):
        @env_property
        def descr(self, v):
            return v

        assert isinstance(descr, EnvDescriptor)
        assert descr.fget
        assert descr.type == str
        assert descr.default == None

    def test_can_create_env_property_with_options(self):
        @env_property(default=42, name='foo')
        def descr(self, v):
            return v

        assert isinstance(descr, EnvDescriptor)
        assert descr.fget
        assert descr.type == int
        assert descr.default == 42
        assert descr.name == 'foo'

    def test_conf_can_access_value(self, conf_class):
        with environ():
            assert conf_class().EPROP == 1

        with environ({'EPROP': '10'}):
            assert conf_class().EPROP == 11


class TestSettings:
    @pytest.fixture(scope='class')
    def conf_class(self):
        class ConfClass(Conf):
            V1 = env(1)
            V2 = env(2.0)
            V3 = env('foo')
            V4 = env(['foo', 'bar'])
            V5 = env(('foo', 'bar'))
            V6 = env({'foo': 'bar'})

            @env_property(default=0)
            def V7(self, value):
                return value + 1

            @env_property(default=0, name='v8')
            def V8(self, value):
                return value + 2

        return ConfClass

    DEFAULT_VALUES = dict(
        V1=1, V2=2.0, V3='foo',
        V4=['foo', 'bar'], V5=('foo', 'bar'), V6={'foo': 'bar'},
        V7=1, V8=2,
    )

    def test_conf_get_settings(self, conf_class):
        conf = conf_class()
        with environ():
            assert conf.load_settings() == self.DEFAULT_VALUES

        assert conf.load_settings() == conf.load_settings()

    def test_save_configurations(self, conf_class):
        ns = {}

        with environ():
            save_configuration(conf_class, ns)
        assert ns == self.DEFAULT_VALUES

    def test_save_configurations_on_settings_module(self, conf_class):
        mod = types.ModuleType('boogie.fake_test_module')

        # Save module
        mod.__dict__.clear()
        with environ():
            save_configuration(conf_class, mod)
        assert mod.__dict__ == self.DEFAULT_VALUES

        # Import module string
        mod.__dict__.clear()
        sys.modules['boogie.fake_test_module'] = mod
        with environ():
            save_configuration(conf_class, 'boogie.fake_test_module')
        assert mod.__dict__ == self.DEFAULT_VALUES

        # DJANGO_SETTINGS_MODULE
        mod.__dict__.clear()
        with environ({'DJANGO_SETTINGS_MODULE': 'boogie.fake_test_module'}):
            save_configuration(conf_class)
        assert mod.__dict__ == self.DEFAULT_VALUES

        del sys.modules['boogie.fake_test_module']


class TestGetterMethods:
    @pytest.fixture(scope='class')
    def conf_class(self):
        class ConfClass(Conf):
            def get_v1(self):
                return 42

            def get_v2(self, v1):
                return v1 + 1

        return ConfClass

    def test_load_variables(self, conf_class):
        assert conf_class().load_settings() == {'V1': 42, 'V2': 43}


class TestDjangoSettings:
    def test_django_conf_create_minimum_configuration(self):
        conf = DjangoConf()
        settings = conf.load_settings()
        from pprint import pprint; pprint(settings)

        assert {
            'ADMIN_URL',
            'ALLOWED_HOSTS',
            'AUTH_PASSWORD_VALIDATORS',
            'BASE_DIR',
            'DATABASES',
            'DEBUG',
            'DJANGO_TEMPLATES',
            'ENVIRONMENT',
            'INSTALLED_APPS',
            'JINJA_TEMPLATES',
            'LANGUAGE_CODE',
            'MIDDLEWARE',
            'ROOT_URLCONF',
            'SECRET_KEY',
            'SERVE_STATIC_FILES',
            'STATIC_URL',
            'TEMPLATES',
            'TIME_ZONE',
            'USE_I18N',
            'USE_L10N',
            'USE_TZ',
            'WSGI_APPLICATION'
        } - set(settings) == set()

    def test_secret_key_is_deterministic(self):
        conf1 = DjangoConf(environment='production')
        conf2 = DjangoConf(environment='production')
        assert conf1.load_settings()['SECRET_KEY'] == \
               conf2.load_settings()['SECRET_KEY']


