import ForceChangePassword from '../../../src/components/common/force-change-password/force-change-password';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'ForceChangePassword',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <ForceChangePassword onPasswordChange={() => {}} />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
