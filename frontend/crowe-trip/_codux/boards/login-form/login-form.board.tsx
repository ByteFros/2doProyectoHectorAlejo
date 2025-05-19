import  LoginForm  from '../../../src/components/login-form/login-form';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'LoginForm',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <LoginForm />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
