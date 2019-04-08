from ..base import Conf


class Pipeline(Conf):
    get_pipeline_enabled = lambda self: not self.DEBUG
    get_pipeline_collector_enabled = lambda self: True

    def get_pipeline(self):
        """
        Return pipeline configuration.
        """
        result = {
            "PIPELINE_ENABLED": self.PIPELINE_ENABLED,
            "PIPELINE_COLLECTOR_ENABLED": self.PIPELINE_COLLECTOR_ENABLED,
        }
        for section in ["JAVASCRIPT", "STYLESHEETS"]:
            contents = getattr(self, "PIPELINE_" + section, None)
            if contents is not None:
                result[section] = contents
        return result

    #
    # Integrations
    #
    def get_jinja_extensions(self):
        return [*super().get_jinja_extensions(), "pipeline.jinja2.PipelineExtension"]
