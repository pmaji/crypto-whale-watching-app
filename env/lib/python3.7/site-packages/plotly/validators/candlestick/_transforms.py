import _plotly_utils.basevalidators


class TransformsValidator(_plotly_utils.basevalidators.CompoundArrayValidator):

    def __init__(
        self, plotly_name='transforms', parent_name='candlestick', **kwargs
    ):
        super(TransformsValidator, self).__init__(
            plotly_name=plotly_name,
            parent_name=parent_name,
            data_class_str='Transform',
            data_docs="""""",
            **kwargs
        )
