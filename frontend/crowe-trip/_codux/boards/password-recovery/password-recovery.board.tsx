import PasswordRecovery from '../../../src/components/password-recovery/password-recovery';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'PasswordRecovery',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <PasswordRecovery
                    onBack={function (): void {
                        throw new Error('Function not implemented.');
                    }}
                />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
