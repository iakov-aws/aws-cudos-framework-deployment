import questionary
import boto3

from botocore.exceptions import NoCredentialsError, CredentialRetrievalError, NoRegionError

import logging
logger = logging.getLogger(__name__)

params = {} # parameters from command line

def get_aws_region():
    return get_boto_session().region_name

def get_boto_session(**kwargs):
    """
    Initiates boto's session object
    :param region: region name
    :param args: arguments
    :return: Boto3 Client
    """
    try:
        session = boto3.session.Session(**kwargs)
        logger.info('Boto3 session created')
        logger.debug(session)
        if not session.region_name:
            raise NoRegionError
        return session
    except (NoCredentialsError, CredentialRetrievalError):
        print('Error: unable to initialize session, please check your AWS credentials, exiting')
        exit(1)
    except NoRegionError:
        logger.info('No AWS region set, defaulting to us-east-1')
        kwargs.update({'region_name': 'us-east-1'})
        return get_boto_session(**kwargs)
    except Exception as e:
        logger.debug(e, stack_info=True)
        raise

def get_boto_client(service_name, **kwargs):
    """
    Initiates boto's client object
    :param service_name: service name
    :param region: region name
    :param args: arguments
    :return: Boto3 Client
    """
    try:
        session = get_boto_session(**kwargs)
        return session.client(service_name)
    except (NoCredentialsError, CredentialRetrievalError):
        print('Error: unable to initialize boto client, please check your AWS credentials, exiting')
        exit(1)
    except Exception as e:
        logger.debug(e, stack_info=True)
        raise

def set_parameters(parameters):
    for k, v in parameters.items():
        params[k.replace('_', '-')] = v

def get_parameters():
    return dict(params)

def get_parameter(param_name, message, choices=None, default=None, none_as_disabled=False, template_variables={}, break_on_ctrl_c=True):
    """ 
    Check if parameters are provided in the command line and if not, ask user 

    :param message: text message for user
    :param choices: a list or dict for choice. None for text entry
    :param default: a default text template
    :param none_as_disabled: if True and choices is a dict, all choices with None as a value will be disabled
    :param template_variables: a dict with varibles for template
    :param break_on_ctrl_c: if True, exit() if user pressed CTRL+C

    :returns: a value choosed by user or provided in command line    
    """
    param_name = param_name.replace('_', '-')
    if param_name in params:
        value = params[param_name]
        logger.info(f'Using {param_name}={value}, from parameters')
        return value.format(**template_variables) 

    if choices is not None:
        if isinstance(choices, dict):
            _choices = []
            for key, value in choices.items():
                print(key, value)
                _choices.append(
                    questionary.Choice(
                        title=key,
                        value=value,
                        disabled=True if (none_as_disabled and value is None) else False,
                    )
                )
                choices = _choices
        print()
        result = questionary.select(
            message=f'[{param_name}] {message}:',
            choices=choices,
            default=default,
        ).ask()
    else: # it is a text entry
        if default:
            default=default.format(**template_variables)
        print()
        result = questionary.text(
            message=f'[{param_name}] {message}:' ,
            default=default or '',
        ).ask()
        if result:
            result = result.format(**template_variables)
    if (break_on_ctrl_c and result is None):
        exit(1)
    print(f"(Use \033[1m --{param_name} '{result}'\033[0m next time you run this)")
    params[param_name] = result
    return result
