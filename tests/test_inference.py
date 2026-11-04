import json
import tempfile
import unittest
from unittest.mock import patch
from spark_control.config import Config
from spark_control.services import Services
from spark_control.inference import Inference, decode, prometheus


class InferenceTests(unittest.TestCase):
    def test_restart_with_model_endpoint_failure_does_not_reuse_old_context(self):
        with tempfile.TemporaryDirectory() as directory:
            svc=Services(Config(directory))
            svc.registry.apply(dict(registry_schema=1,revision=0,services=[dict(id='llm',name='LLM',adapter='openai-compatible',default_profile_id='profile')],profiles=[dict(id='profile',service_id='llm',name='default',manager={'type':'systemd-user','unit':'test-llm.service'},probe={'origin':'http://127.0.0.1:18888'})]),0)
            row=dict(id='llm',adapter='openai-compatible',state='running',profile_id='profile')
            clock=[100.0]; invocation=['one']
            def fetch(base,path,*args):
                if path=='/metrics':return 'vllm:generation_tokens_total 100'
                if invocation[0]=='two':raise OSError('endpoint temporarily unavailable')
                return '{"data":[{"id":"model-a","max_model_len":4096}]}'
            with patch.object(svc,'listing',return_value={'services':[row]}),patch('spark_control.inference.fetch',side_effect=fetch),patch('spark_control.inference.system_states',side_effect=lambda u:{u[0]:{'InvocationID':invocation[0]}}),patch('spark_control.inference.time.monotonic',side_effect=lambda:clock[0]):
                collector=Inference(svc)
                self.assertEqual(collector.snapshot()['current']['context'],4096)
                clock[0]+=5;invocation[0]='two'
                result=collector.snapshot()
                self.assertIsNone(result['current']['context'])
                self.assertIsNone(result['current']['model'])

    def test_supported_formats_and_unknown(self):
        self.assertEqual(decode('unrecognized')['engine'],'unsupported')
        value=decode('vllm:generation_tokens_total{model_name="test"} 100\nvllm:num_requests_running 2')
        self.assertEqual(value['output_total'],100)
        self.assertEqual(value['running'],2)
        self.assertIsNone(value['input_total'])
        value=decode(json.dumps(dict(engine={'max_context':4096},live={'state':'generating','tok_s':52,'running':1,'queued':2,'waiting':2},totals={'output_tokens':400})))
        self.assertEqual(value['output_rate'],52)
        self.assertEqual(value['waiting'],2) # overlapping queued/waiting must not be summed
        value=decode('tensorfold:generation_tokens_total 100\ntensorfold:generation_tokens_running 20',{'live':{'decode_tokens_per_second':8}})
        self.assertEqual(value['live_total'],120)
        self.assertEqual(value['output_rate'],8)
        self.assertNotIn('bad',prometheus('bad NaN\nbad Infinity'))

    def test_shared_cache_reset_gaps_and_running_counter_transfer(self):
        with tempfile.TemporaryDirectory() as directory:
            svc=Services(Config(directory))
            svc.registry.apply(dict(registry_schema=1,revision=0,services=[dict(id='llm',name='LLM',adapter='openai-compatible',default_profile_id='profile')],profiles=[dict(id='profile',service_id='llm',name='default',manager={'type':'systemd-user','unit':'test-llm.service'},probe={'origin':'http://127.0.0.1:18888'})]),0)
            row=dict(id='llm',adapter='openai-compatible',state='running',profile_id='profile')
            clock=[100.0]; totals=[100,20]; invocation=['one']; fail=[False]
            def fetch(base,path,*args):
                if fail[0]: raise OSError('private detail must not escape')
                if path=='/metrics':return f'tensorfold:generation_tokens_total {totals[0]}\ntensorfold:generation_tokens_running {totals[1]}\ntensorfold:prompt_tokens_total 10'
                if path=='/v1/models':return '{"data":[{"id":"/private/model/path"}]}'
                return '{}'
            with patch.object(svc,'listing',return_value={'services':[row]}),patch('spark_control.inference.fetch',side_effect=fetch) as probe,patch('spark_control.inference.system_states',side_effect=lambda u:{u[0]:{'InvocationID':invocation[0]}}),patch('spark_control.inference.time.monotonic',side_effect=lambda:clock[0]):
                collector=Inference(svc)
                first=collector.snapshot();self.assertIsNone(first['current']['output_rate']);self.assertIsNone(first['current']['model'])
                calls=probe.call_count;collector.snapshot();self.assertEqual(probe.call_count,calls)
                clock[0]+=5;totals[1]=70
                self.assertEqual(collector.snapshot()['current']['output_rate'],10)
                clock[0]+=5;totals[1]=0 # running gauge drops before finished counter updates
                self.assertEqual(collector.snapshot()['current']['output_rate'],0)
                clock[0]+=5;totals[0]=170
                self.assertEqual(collector.snapshot()['current']['output_rate'],0)
                clock[0]+=20;totals[1]=40
                self.assertIsNone(collector.snapshot()['current']['output_rate'])
                clock[0]+=5;fail[0]=True
                result=collector.snapshot();self.assertEqual(result['status'],'unavailable');self.assertNotIn('private detail',json.dumps(result))
                clock[0]+=5;fail[0]=False
                self.assertIsNone(collector.snapshot()['current']['output_rate'])
                clock[0]+=5;totals[0]=0;totals[1]=0;invocation[0]='two'
                result=collector.snapshot();self.assertIsNone(result['current']['output_rate']);self.assertEqual(len(result['history']),1)
                self.assertLessEqual(len(collector.streams),4)
