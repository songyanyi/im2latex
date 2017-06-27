# -*- coding: utf-8 -*-
"""
    Copyright 2017 Sumeet S Singh

    This file is part of im2latex solution by Sumeet S Singh.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the Affero GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    Affero GNU General Public License for more details.

    You should have received a copy of the Affero GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Tested on python 2.7

@author: Sumeet S Singh
"""
import copy

class AccessDeniedError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
    
"""
A shorthand way to create a class with
several properties without having to hand-code the getter and setter functions.
getter/setter access is automatically provided saving you from having to write
two decorated functions (getter and setter) per property.
The properties can either be provided at init time or added on the fly simply
by setting/assigning them.
You can also view this as a javascript Object style dictionary because it allows
both attribute getter/setter as well as dictionary accessor (square brackets) syntax.
Additionally, you my call freeze() or seal() to freeze or seal
the dictionary - just as in Javascript.
The class inherits from dict therefore all standard python dictionary interfaces
are available as well (such as iteritems etc.)

x = Dictionary({'x':1, 2:'y'})
assert d.x == d['x']
d.x = 5
assert d['x'] == 5
d.seal()
d[3] = 'z' # okay, new property created
assert d.3 == 'z'
d[2] = 'a' # raises AccessDeniedError
d.freeze()
d[4] = 'a' # raises AccessDeniedError
d[2] = 'a' # raises AccessDeniedError
"""
class Properties(dict):
    def __init__(self, d={}):
        dict.__init__(self, d)
        object.__setattr__(self, '_isFrozen', False)
        object.__setattr__(self, '_isSealed', False)
        
    def _get_val_(self, key):
        return dict.__getitem__(self, key)
            
    def _set_val_(self, key, val):
        if self.isFrozen():
            raise AccessDeniedError('Object is frozen, therefore key "%s" cannot be modified'%(key,))
        elif self.isSealed() and key not in dict.keys(self):
            raise AccessDeniedError('Object is sealed, new key "%s" cannot be added'%(key,))
        else:
            dict.__setitem__(self, key, val)
    
    def __copy__(self):
        return dict.copy(self)
    
    def __getattr__(self, key):
        return self._get_val_(key)
    
    def __setattr__(self, key, val):
        return self._set_val_(key, val)
    
    def __getitem__(self, key):
        return self._get_val_(key)
    
    def __setitem__(self, key, val):
        return self._set_val_(key, val)
    
    def isFrozen(self):
        return object.__getattribute__(self, '_isFrozen')
    
    def isSealed(self):
        return object.__getattribute__(self, '_isSealed')

    def freeze(self):
        object.__setattr__(self, '_isFrozen', True)
        return self

    def seal(self):
        object.__setattr__(self, '_isSealed', True)
        return self

# A validator that returns False for non-None values
class _mandatoryValidator(object):
    def __contains__(self, val):
        return val is not None

mandatory = _mandatoryValidator()

class instanceof(object):
    def __init__(self, cls):
        self._cls = cls
    def __contains__(self, obj):
        return isinstance(obj, self._cls)

# A float range validator class
class frange_incl(object):
    def __init__(self, begin, end):
        self._begin = begin
        self._end = end
    def __contains__(self, f):
        return f <= self._end and f >= self._begin

"""
A property descriptor.
"""
class ParamDesc(Properties):
    """ 
    @name = name of property,
    @text = textual description, 
    @validator = (optional) a validator object that implements the __contains__()
        method so that membership may be inspected using the 'in' operator - 
        as in 'if val in validator:'
    @default = value (optional) stands for the default value. Set to None if
        unspecified.
    
    The object gets immediately frozen after
    initialization so that the property descriptor can be re-used repeatedly
    without fear of modification.
    """
    def __init__(self, name, text, validator=None, default=None):
        Properties.__init__(self, {'name':name, 'text':text, 'validator':validator, 'default':default})
        self.freeze()
    
"""
Prototyped Properties class. The prototype is passed into the constructor and
should be a list of ParamDesc objects denoting all the allowed properties.
No new properties can be added in the future - i.e. the object is sealed.
You may also freeze the object at any point if you want.
This class is used to define and store descriptors of a model. It inherits
from class Properties.
"""
class Params(Properties):
    """
    Takes property descriptors and their values. After initialization, no new params
    may be created - i.e. the object is sealed (see class Properties). The
    property values can be modified however (unless you call freeze()).
    
    @prototype Supplies list of ParamDesc objects which serve as the list of
        valid properties. Can be a sequence of ParamDesc objects or another Params object.
        If it was a Params object, then descriptors would be derived
        from prototype.protoS.
        This object will also provide the property values if not specified in
        the vals argument (below). If this was a list of ParamDesc objects,
        then the default property values would be used (ParamDesc.default). If
        on the other hand, this was a Params object, then its property
        value would be used (i.e. the return value of Params['prop_name']).
        
    @initVals Optional; provides initial values of the properties of this object.
        May specify a subset of the object's properties, or none at all. Unspecified
        property values will be initialized from the prototype object.
        Should be either a dictionary of name:value pairs or unspecified (None).
    
    Examples:
    o1 = Params(
                [
                 ParamDesc('model_name', 'Name of Model', None, 'im2latex'),
                 ParamDesc('layer_type', 'Type of layers to be created'),
                 ParamDesc('num_layers', 'Number of layers. Defaults to 1', xrange(1,101), 1)
                ])
    o2 = Params(o1) # copies prototype from o1, uses default values
    o3 = Params(o1, initVals={'model_name':'im2latex'}) # uses descriptors from o1.protoS,
        initializes with val from vals if available otherwise with default from o1.protoS
    """
    def __init__(self, prototype, initVals=None):
        Properties.__init__(self)
        descriptors = prototype
        props = Properties()
        vals1_ = {}
        vals2_ = {}
        _vals = {}
        
        if isinstance(prototype, Params):
            descriptors = prototype.protoS
            if initVals is None:
                vals1_ = prototype
            else:
                vals1_ = initVals
                vals2_ = prototype
        else:
            if initVals is None:
                vals1_ = {}
            else:
                vals1_ = initVals

        object.__setattr__(self, '_desc_list', tuple(descriptors) )

        for prop in descriptors:
            name = prop.name
            if name not in props:
                props[name] = prop
                _vals[name] = vals1_[name] if (name in vals1_) else vals2_[name] if (name in vals2_) else prop.default
            else:
                raise ValueError('property %s has already been initialized'%(name,))

        object.__setattr__(self, '_descr_dict', props.freeze())

        # Now insert the property values one by one. Doing so will invoke
        # self._set_val_ which will validate the initial values against self._descr_dict.

        for _name, _val in _vals.iteritems():
            self[_name] = _val        

        # Finally, seal the object so that no new properties may be added.
        self.seal()
                        
    """ Polymorphic override of _set_val_. Be careful of recursion. """
    def _set_val_(self, name, val):
        protoD = self.protoD
        if not self.isValidName(name):
            raise KeyError('%s is not an allowed property name'%(name,))
        # As a special case, we allow setting None values even if that's not an 
        # allowed value. This is so because the code may want to set the
        # property value in the future based on some dynamic decision.
        elif (val is not None) and (protoD[name].validator is not None) and (val not in protoD[name].validator):
            raise ValueError('%s is not a valid value of property %s'%(val, name))
        else:
            return Properties._set_val_(self, name, val)

    """ Polymorphic override of _get_val_. Be careful of recursion. """
    def _get_val_(self, name):
        if not self.isValidName(name):
            raise KeyError('%s is not an allowed property name'%(name,))
        else:
            return Properties._get_val_(self, name)
    
    def isValidName(self, name):
        return name in self.protoD
    
    @property
    def protoS(self):
        # self._desc_list won't recursively call _get_val_ because __getattribute__ will return successfully
        #return self._desc_list
        return object.__getattribute__(self, '_desc_list')
    
    @property
    def protoD(self):
        # self._descr_dict won't call __getattr__ because __getattribute__ returns successfully
        #return self._descr_dict
        return object.__getattribute__(self, '_descr_dict')

"""
Params class specialized for HyperParams. Adds the following semantic:
    If a key has value None, then it is deemed absent from the dictionary. Calls
    to __contains__ and _get_val_ will beget a KeyError - as if the property was
    absent from the dictionary. This is necessary to catch cases wherein one
    has forgotten to set a mandatory property. Mandatory properties must not have
    default values in their descriptor. A property that one is okay forgetting
    to specify should have a None default value set in its descriptor which may
    include 'None'.
    However as with Params, it is still possible to initialize or set a property value to
    None eventhough None may not appear in the valid-list. We allow this in
    order to enable lazy initialization - i.e. a case where the
    code may wish to initialize a property to None, and set it to a valid value
    later. Setting a property value to None tantamounts to unsetting / deleting
    the property.
"""        
class HyperParams(Params):

    """ Handles None values in a special way as stated above. """
    def __contains__(self, name):
        try:
            self._get_val_(name)
            return True
        except KeyError:
            return False
    
    """ Polymorphic override of _get_val_. Be careful of recursion. """
    def _get_val_(self, name):
        val = Params._get_val_(self, name)
        validator = self.protoD[name].validator
        if (val == None) and ((validator is None) or (None not in validator)):
            raise KeyError('property %s was not set'%(name,))
        else:
            return val
