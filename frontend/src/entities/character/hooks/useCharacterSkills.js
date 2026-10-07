import { 
  useGetCharacterSkillsQuery,
  useAddCharacterSkillsMutation 
} from '../api/characterApi';


/**
 * Домен навыков: загрузка + сохранение.
 * Открытие модалки — через setActiveModal('SKILLS_MODAL').
 */
export const useCharacterSkills = (setActiveModal) => {
  const [addSkills] = useAddCharacterSkillsMutation();

  const { data: skillsData } = useGetCharacterSkillsQuery();

  // ИСПРАВЛЕНО: count_stats и count_mastership — это ЧИСЛА, не массивы
  const abilitySkills = skillsData?.count_stats || 0;
  const weaponSkills = skillsData?.count_mastership || 0;
  const isShowUpSkills = abilitySkills > 0 || weaponSkills > 0;

  const handleUpSkillsButtonClick = () => {
    setActiveModal('SKILLS_MODAL');
  };

  const handleSaveUpSkills = async (data) => {
    try {
      await addSkills(data).unwrap();
    } catch (error) {
      console.error('Ошибка добавления навыков:', error);
      throw error;
    }
  };

  return {
    abilitySkills,
    weaponSkills,
    isShowUpSkills,    
    handleUpSkillsButtonClick,
    handleSaveUpSkills,
  };
};