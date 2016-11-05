﻿# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

from . import cntk_py
from . import trainer
from .utils import typemap

# Preload libmpi.so for non-Windows platform to work around MPI_Init failure bug
# https://xrunhprof.wordpress.com/2014/11/04/an-openmpi-python-and-dlopen-issue/
# If other OS has similar OpenMPI MPI_Init failure, add dll load to global here
import platform
import ctypes
if platform.system() == 'Linux':
    ctypes.CDLL("libmpi.so", mode=ctypes.RTLD_GLOBAL)

__doc__= '''\
Distributed trainers manage trainers in distributed environment.
'''

class WorkerDescriptor(cntk_py.DistributedWorkerDescriptor):
    '''
    Distributed worker descriptor, returned by :class:`Communicator` instance.
    '''

    @property
    def global_rank(self):
        '''
        The global rank of the worker.
        '''
        return super().m_global_rank

    @property
    def host_id(self):
        '''
        The host id of the worker.
        '''
        return super().m_host_id

class Communicator(cntk_py.DistributedCommunicator):
    '''
    A communicator interface exposing communication primitives that serve as building blocks 
    for distributed training.
    '''

    @typemap
    def workers(self):
        '''
        Returns workers in this communicator.
        
        Returns:
            (`list`) of :class:`WorkerDescriptor`: workers in this communicator.
        '''
        return super().workers()

    @typemap
    def current_worker(self):
        '''
        Returns worker descriptor of current process.
        
        Returns:
            :class:`WorkerDescriptor`: descriptor of current process.
        '''
        return super().current_worker()

    def barrier(self):
        '''
        sync point to make sure all workers reach the same state
        '''
        super().barrier()
        
    @staticmethod
    def finalize():
        '''
        calls MPI_Finalize(), and no more communication can happen afterwards
        '''
        cntk_py.DistributedCommunicator.finalize()
        
class DistributedTrainer(cntk_py.DistributedTrainer):
    '''
    A distributed trainer that handles data like gradients/momentums across multiple MPI workers
    '''
    
    @typemap
    def communicator(self):
        '''
        Returns the distributed communicator that talks to other MPI workers
        
        Returns:
            :class:`Communicator`: descriptor of current process.
        '''
        return super().get_communicator()
        
    @property
    def parallelization_start_after_sample_count(self):
        '''
        number of samples to process, then parallelization starts
		'''
        return super().get_parallelization_start_after_sample_count()

@typemap
def data_parallel_distributed_trainer(use_async_buffered_parameter_update=False, num_quantization_bits=32, parallelization_start_after_sample_count=0):
    '''
    Creates a data parallel distributed trainer using `communicator` with
    option `use_async_buffered_parameter_update`.

    Args:
        communicator: a communicator or a quantized communicator
        use_async_buffered_parameter_update (`bool`): use async buffered parameter update

    Returns:
        a distributed trainer instance
    '''
    if (num_quantization_bits < 32):
        return cntk_py.create_quantized_data_parallel_distributed_trainer(
            cntk_py.quantized_mpicommunicator(True, True, num_quantization_bits),
            use_async_buffered_parameter_update,
            parallelization_start_after_sample_count)
    else:
        return cntk_py.create_data_parallel_distributed_trainer(
            cntk_py.mpicommunicator(),
            use_async_buffered_parameter_update,
            parallelization_start_after_sample_count)