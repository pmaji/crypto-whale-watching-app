from plotly.basedatatypes import BaseTraceHierarchyType


class Transform(BaseTraceHierarchyType):

    # property parent name
    # --------------------
    @property
    def _parent_path_str(self):
        return 'scattermapbox'

    # Self properties description
    # ---------------------------
    @property
    def _prop_descriptions(self):
        return """\
        """

    def __init__(self, **kwargs):
        """
        Construct a new Transform object
        
        An array of operations that manipulate the trace data, for
        example filtering or sorting the data arrays.

        Parameters
        ----------

        Returns
        -------
        Transform
        """
        super(Transform, self).__init__('transforms')

        # Import validators
        # -----------------
        from plotly.validators.scattermapbox import (transform as v_transform)

        # Initialize validators
        # ---------------------

        # Populate data dict with properties
        # ----------------------------------

        # Process unknown kwargs
        # ----------------------
        self._process_kwargs(**kwargs)
