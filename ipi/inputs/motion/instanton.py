"""Deals with creating the ensembles class.

Copyright (C) 2013, Joshua More and Michele Ceriotti

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http.//www.gnu.org/licenses/>.

Classes:
   InputInst: Deals with creating the Inst object from a file, and
      writing the checkpoints.
"""

import numpy as np
from ipi.utils.inputvalue import *


__all__ = ['InputInst']

class InputInst(InputDictionary):
    """Instanton optimization options.

    Contains options related with instanton, such as method,
    thresholds, hessian update strategy, etc.

    """
    attribs={"mode"  : (InputAttribute, {"dtype"   : str, "default": "rate",
                                    "help"    : "Use the full or half of the ring polymer during the optimization",
                                    "options" : ['rate','splitting']}) }

    fields = {"tolerances" : ( InputDictionary, {"dtype" : float,
                              "options"  : [ "energy", "force", "position" ],
                              "default"  : [ 1e-5, 1e-5, 6e-3 ],
                              "help"     : "Convergence criteria for optimization.",
                              "dimension": [ "energy", "force", "length" ] }),
               "biggest_step": (InputValue, {"dtype" : float,
                              "default"  : 0.4,
                              "help"     : "The maximum step size during the optimization."}),
               "old_pos":    (InputArray, {"dtype" : float,
                              "default"  : input_default(factory=np.zeros, args = (0,)),
                              "help"     : "The previous step positions during the optimization. ",
                              "dimension": "length"}),
               "old_pot":    (InputArray, {"dtype" : float,
                              "default"  : input_default(factory=np.zeros, args = (0,)),
                              "help"     : "The previous step potential energy during the optimization",
                              "dimension": "energy"}),
               "old_force":  (InputArray, {"dtype" : float,
                              "default"  : input_default(factory=np.zeros, args = (0,)),
                              "help"     : "The previous step force during the optimization",
                              "dimension": "force"}),
               "opt": (InputValue, {"dtype": str,
                                            "default": 'None',
                                            "options": ["nichols","lbfgs",'None'],
                                            "help": "The geometry optimization algorithm to be used"}),
               "action": (InputArray, {"dtype": float,
                                      "default": input_default(factory=np.zeros, args=(0,)),
                                      "help": "Vector containing the 2  components ('spring' and 'physical') of the actions. Unitless "}),
               "prefix": (InputValue, {"dtype": str,
                                      "default": "INSTANTON",
                                      "help": "Prefix of the output files."}),
               "delta": (InputValue, {"dtype": float,
                                     "default": 0.1,
                                     "help": "Initial stretch amplitude."}),
               "hessian_sparse": (InputValue, {"dtype": str,
                                          "default": "false",
                                          "options": ["false", "true"],
                                          "help": "Decide if we work with sparse numerical algorithm or not."}),
               "hessian_init": (InputValue, {"dtype": str,
                                            "default": 'None',
                                            "options": ["true", 'None'],
                                            "help": "How to initialize the hessian if it is not fully provided."}),
               "hessian":    (InputArray, {"dtype" : float,
                              "default"  : input_default(factory=np.eye, args = (0,)),
                              "help"     : "(Approximate) Hessian."}),
               "hessian_update": (InputValue, {"dtype": str,
                                "default": "powell",
                                "options": ["powell", "recompute"],
                                "help": "How to update the hessian in each step."}),
               "hessian_asr": (InputValue, {"dtype": str,
                                "default": "none",
                                "options": ["none","poly","crystal"],
                                "help": "Removes the zero frequency vibrational modes depending on the symmerty of the system."}),
               "qlist_lbfgs": (InputArray, {"dtype": float,
                                           "default": input_default(factory=np.zeros, args=(0,)),
                                           "help": "List of previous position differences for L-BFGS, if known."}),
               "glist_lbfgs": (InputArray, {"dtype": float,
                                           "default": input_default(factory=np.zeros, args=(0,)),
                                           "help": "List of previous gradient differences for L-BFGS, if known."}),
               "scale_lbfgs": (InputValue, {"dtype": int,
                                           "default": 2,
                                           "help": """Scale choice for the initial hessian.
                                                       0 identity.
                                                       1 Use first member of position/gradient list. 
                                                       2 Use last  member of position/gradient list."""}),
               "corrections_lbfgs": (InputValue, {"dtype": int,
                                                 "default": 6,
                                                 "help": "The number of past vectors to store for L-BFGS."}),
               "final_post": (InputValue, {"dtype": str,
                                          "default": "false",
                                          "options": ["false", "true"],
                                          "help": "Decide if we are going to compute the final big-hessian by finite difference."})
}

    dynamic = {  }

    default_help = "TODO EXPLAIN WHAT THIS IS"
    default_label = "Instanton"

    def store(self, geop):
        if geop == {}: 
            return

        # Optimization mode
        self.mode.store(geop.mode)

        # Generic optimization
        self.tolerances.store(geop.tolerances)
        self.biggest_step.store(geop.big_step)
        self.opt.store(geop.opt)

        # Generic instanton
        self.action.store(geop.action)
        self.prefix.store(geop.prefix)
        self.delta.store(geop.delta)
        self.final_post.store(geop.final_post)


        if geop.mode =='rate':
            #self.hessian_init.store(geop.hessian_init)
            self.hessian_sparse.store(geop.sparse)
            self.hessian.store(geop.hessian)
            self.hessian_update.store(geop.hessian_update)
            self.hessian_asr.store(geop.hessian_asr)
        elif geop.mode =='splitting':
            self.qlist_lbfgs.store(geop.qlist)
            self.glist_lbfgs.store(geop.glist)
            self.corrections_lbfgs.store(geop.corrections)
            self.scale_lbfgs.store(geop.scale)



    def fetch(self):
        rv = super(InputInst,self).fetch()
        rv["mode"] = self.mode.fetch()
        return rv
