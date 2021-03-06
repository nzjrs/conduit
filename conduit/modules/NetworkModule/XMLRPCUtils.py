"""
Utilty functions shared between the xml-rpc client and server

Copyright: John Stowers, 2006
License: GPLv2
"""
import socket
import select
import traceback
import threading
import cPickle
import xmlrpclib
import SimpleXMLRPCServer
import logging
import time

#One log for the client
clog = logging.getLogger("modules.Network.C")
#One log for the server
slog = logging.getLogger("modules.Network.S")

import conduit.Exceptions as Exceptions
import conduit.dataproviders.DataProvider as DataProvider
import conduit.utils as Utils

XML_RPC_EASY_EXCEPTIONS = (
    "RefreshError",
    "SyncronizeError",
    "SyncronizeFatalError",
    "StopSync"
    )
    
def marshal_fault_to_exception(fault, **kwargs):
    if fault.faultCode in XML_RPC_EASY_EXCEPTIONS:
        klass = getattr(Exceptions,fault.faultCode)
        #exception.message = fault.faultString
        raise klass(fault.faultString)
    elif fault.faultCode == "SynchronizeConflictError":
        fromData = kwargs['server'].get(kwargs['fromDataLUID'])
        toData = kwargs['toData']
        raise Exceptions.SynchronizeConflictError(fault.faultString, fromData, toData)
    else:
        raise Exception("Remote Exception:\n%s" % fault.faultString)

def marshal_exception_to_fault(exception):
    klassName = exception.__class__.__name__
    if klassName in XML_RPC_EASY_EXCEPTIONS:
        #exception.message = fault.faultString
        raise xmlrpclib.Fault(klassName, exception.message)
    elif klassName == "SynchronizeConflictError":
        #only put the comparison in the fault, getting the other data 
        #requires subsequent xmlrpc calls
        raise xmlrpclib.Fault("SynchronizeConflictError", exception.comparison)    
    else:
        raise xmlrpclib.Fault("Exception",traceback.format_exc())

def pickle_obj_to_binary(obj):
    bin = xmlrpclib.Binary(cPickle.dumps(obj))
    return bin

def unpickle_obj_from_binary(bin):
    obj = cPickle.loads(bin.data)
    return obj

class StoppableXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
    """
    A variant of SimpleXMLRPCServer that can be stopped. From
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/520583
    """
    allow_reuse_address = True
    def __init__( self, host, port):
        SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self,
                                addr=(host,port),
                                logRequests=False,
                                allow_none=True
                                )
        self.closed = False
    
    def serve(self):
        self.socket.setblocking(0)
        while not self.closed:
            time.sleep(0.15)
            try:
                self.handle_request()
            except TypeError:
                #Python 2.6 throws this on close...
                pass
            except:
                slog.critical("Error handling request", exc_info=True)
            
    def get_request(self):
        inputObjects = []
        while not inputObjects and not self.closed:
            try:
                inputObjects, outputObjects, errorObjects = select.select([self.socket], [], [], 0.2)
                sock, addr = self.socket.accept()
                return (sock, addr)
            except socket.timeout:
                if self.closed:
                    raise
            except socket.error:
                #Occurs at shutdown, raise to stop serving
                if self.closed:
                    raise
            except select.error:
                #Occurs sometimes at start up, race condition, ignore
                pass
                
    def start(self):
        threading.Thread(target=self.serve).start()
        
    def stop(self):
        self.closed = True

class DataProviderClient(DataProvider.TwoWay):
    """
    Provides the Client portion of dataprovider proxying.
    """
    _configurable_ = False
    def __init__(self, *args):
        DataProvider.TwoWay.__init__(self)
        clog.info("Connecting to remote DP on %s" % self.url)
        #Add use_datetime arg for >= python 2.5
        self.server = xmlrpclib.Server(
                                    self.url,
                                    allow_none=True)

    @Utils.log_function_call(clog)
    def refresh(self):
        DataProvider.TwoWay.refresh(self)
        try:
            self.server.refresh()
        except xmlrpclib.Fault, f:
            marshal_fault_to_exception(f)

    @Utils.log_function_call(clog)
    def get_all(self):
        DataProvider.TwoWay.get_all(self)
        try:
            return self.server.get_all()
        except xmlrpclib.Fault, f:
            marshal_fault_to_exception(f)

    @Utils.log_function_call(clog)
    def get(self, LUID):
        DataProvider.TwoWay.get(self, LUID)
        try:
            binaryData = self.server.get(LUID)
            return unpickle_obj_from_binary(binaryData)
        except xmlrpclib.Fault, f:
            marshal_fault_to_exception(f)

    @Utils.log_function_call(clog)
    def put(self, data, overwrite=False, LUID=None):
        DataProvider.TwoWay.put(self, data, overwrite, LUID)
        binaryData = pickle_obj_to_binary(data)
        try:
            binaryRid = self.server.put(binaryData, overwrite, LUID)
            return unpickle_obj_from_binary(binaryRid)
        except xmlrpclib.Fault, f:
            #Supply additional info because the conflict exception
            #includes details of the conflict
            #FIXME: Check from and to isnt backwards...
            marshal_fault_to_exception(
                            f,
                            server=self,
                            fromDataLUID=LUID,
                            toData=data
                            )

    @Utils.log_function_call(clog)
    def delete(self, LUID):
        DataProvider.TwoWay.delete(self, LUID)
        try:
            return self.server.delete(LUID)
        except xmlrpclib.Fault, f:
            marshal_fault_to_exception(f)

    @Utils.log_function_call(clog)
    def finish(self, aborted, error, conflict):
        DataProvider.TwoWay.finish(self)
        try:
            self.server.finish(aborted, error, conflict)
        except xmlrpclib.Fault, f:
            marshal_fault_to_exception(f)

    @Utils.log_function_call(clog)
    def get_UID(self):
        return self.uid
        
    @Utils.log_function_call(clog)
    def set_status(self, newStatus):
        self.server.set_status(newStatus)

    @Utils.log_function_call(clog)
    def get_status(self):
        return self.server.get_status()
        
    def get_name(self):
        return "Remote %s" % self._name_
        
class DataproviderServer(StoppableXMLRPCServer):
    """
    Wraps a dataproviderwrapper in order to pickle args
    and deal with exceptions in the sync process
    """
    def __init__(self, wrapper, port):
        StoppableXMLRPCServer.__init__(self,'',port)
        slog.info("Starting server for %s on port %s" % (wrapper,port))
        self.port = port
        self.dpw = wrapper
        
        #Additional functions not part of the normal dp api
        self.register_function(self.get_info)

        #register individual functions, not the whole object, 
        #because in some cases we need to pickle function arguments
        #and deal with exceptions
        self.register_function(self.refresh)
        self.register_function(self.get_all)
        self.register_function(self.get)
        self.register_function(self.put)
        self.register_function(self.delete)
        self.register_function(self.finish)
        
        #These functions will never throw exceptions so register them in
        #the module directly
        self.register_function(self.dpw.module.set_status)
        self.register_function(self.dpw.module.get_status)


    def get_info(self):
        """
        Return information about this dataprovider 
        (so that client can show correct icon, name, description etc)
        """
        return {"uid":              self.dpw.get_UID(),
                "name":             self.dpw.name,
                "description":      self.dpw.description,
                "icon":             self.dpw.icon_name,
                "module_type":      self.dpw.module_type,
                "in_type":          self.dpw.in_type,
                "out_type":         self.dpw.out_type,
                "dp_server_port":   self.port                 
                }

    @Utils.log_function_call(slog)
    def refresh(self):
        try:
            self.dpw.module.refresh()
        except Exception, e:
            return marshal_exception_to_fault(e)

    @Utils.log_function_call(slog)
    def get_all(self):
        try:
            return self.dpw.module.get_all()
        except Exception, e:
            return marshal_exception_to_fault(e)

    @Utils.log_function_call(slog)
    def get(self, LUID):
        try:
            return pickle_obj_to_binary(self.dpw.module.get(LUID))
        except Exception, e:
            return marshal_exception_to_fault(e)

    @Utils.log_function_call(slog)
    def put(self, binaryData, overwrite, LUID):
        data = unpickle_obj_from_binary(binaryData)
        try:
            rid = self.dpw.module.put(data, overwrite, LUID)
            return pickle_obj_to_binary(rid)
        except Exception, e:
            return marshal_exception_to_fault(e)

    @Utils.log_function_call(slog)
    def delete(self, LUID):
        try:
            self.dpw.module.delete(LUID)
        except Exception, e:
            return marshal_exception_to_fault(e)

    @Utils.log_function_call(slog)
    def finish(self, aborted, error, conflict):
        try:
            self.dpw.module.finish(aborted, error, conflict)
        except Exception, e:
            return marshal_exception_to_fault(e)

