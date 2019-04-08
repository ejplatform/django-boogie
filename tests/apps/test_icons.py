from boogie.experimental.icons.models import SocialIcon


class TestSocialMediaIcon:
    def test_convert_simple_icon_to_strings(self):
        icon = SocialIcon(social_network="github")
        assert str(icon) == "github"
        assert icon.__html__() == '<i class="fab fa-github"></i>'

    def test_convert_icon_with_url_to_strings(self):
        icon = SocialIcon(
            social_network="github", url="http://github.com/foo/bar/"
        )
        assert str(icon) == "github"
        assert str(icon.icon_tag()) == '<i class="fab fa-github"></i>'
        assert (icon.__html__()
                == '<a href="http://github.com/foo/bar/"><i class="fab fa-github"></i></a>')
